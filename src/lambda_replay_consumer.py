import io
import json
from datetime import datetime
from typing import Optional

import boto3
import polars as pl

from config import (
    SIM_BUCKET,
    RAW_PREFIX,
    SOURCE_PROCESSED_BUCKET,
    PROCESSED_PREFIX,
)
from logger import get_logger

logger = get_logger(__name__)

s3_client = boto3.client("s3")

# Các cột OHLCV gốc cần giữ lại (bỏ các cột feature engineering đã tính sẵn)
BASE_OHLCV_COLS = [
    "Date",
    "Open",
    "High",
    "Low",
    "Close",
    "Adj_Close",   # Trong processed/ đã được rename từ "Adj Close"
    "Volume",
    "Symbol",
    "Year",
    "Asset_Type",
]

# Cache đơn giản trong bộ nhớ Lambda để tránh đọc lại cùng 1 file năm nhiều lần
_year_df_cache: dict[int, pl.DataFrame] = {}


def load_year_from_s3(year: int) -> pl.DataFrame:
    """
    Đọc processed/YEAR.parquet từ SOURCE_PROCESSED_BUCKET.
    """
    if year in _year_df_cache:
        logger.info(f"[Cache HIT] Dùng lại data năm {year} từ memory.")
        return _year_df_cache[year]

    source_key = f"{PROCESSED_PREFIX}{year}.parquet"
    logger.info(f"Đọc s3://{SOURCE_PROCESSED_BUCKET}/{source_key}")

    response = s3_client.get_object(Bucket=SOURCE_PROCESSED_BUCKET, Key=source_key)
    raw_bytes = response["Body"].read()

    df = pl.read_parquet(io.BytesIO(raw_bytes))

    # Chỉ giữ các cột OHLCV gốc (bỏ feature engineering đã tính sẵn)
    available_cols = [c for c in BASE_OHLCV_COLS if c in df.columns]
    df = df.select(available_cols)

    # Đảm bảo cột Date là kiểu pl.Date
    if "Date" in df.columns and df["Date"].dtype != pl.Date:
        df = df.with_columns(pl.col("Date").cast(pl.Date))

    logger.info(f"Đã tải năm {year}: {df.height:,} dòng | {df['Symbol'].n_unique()} tickers")
    _year_df_cache[year] = df
    return df


def filter_day_and_tickers(
    year_df: pl.DataFrame,
    trade_date: str,
    tickers: list[str],
) -> pl.DataFrame:
    """
    Filter DataFrame năm
    """
    trade_date_obj = datetime.strptime(trade_date, "%Y-%m-%d").date()

    df_day = year_df.filter(
        (pl.col("Date") == trade_date_obj) &
        (pl.col("Symbol").is_in(tickers))
    )

    logger.info(
        f"Filter ngày {trade_date} × {len(tickers)} tickers "
        f"→ {df_day.height} dòng ({df_day['Symbol'].n_unique() if df_day.height > 0 else 0} tickers có data)"
    )
    return df_day


def upload_chunk_to_sim(df_day: pl.DataFrame, trade_date: str, chunk_index: int) -> list[str]:
    """
    Ghi DataFrame gộp của cả chunk lên SIM_BUCKET dưới dạng 1 file Parquet duy nhất per chunk.
    Tối ưu hóa: Giảm 99% chi phí S3 PUT requests khi chạy Replay Simulation.
    """
    if df_day.height == 0:
        return []

    # Đổi tên lại để tương thích với Quality Gate (expects "Adj Close")
    df_out = df_day
    if "Adj_Close" in df_out.columns:
        df_out = df_out.rename({"Adj_Close": "Adj Close"})

    s3_key = f"{RAW_PREFIX}{trade_date}/chunk_{chunk_index if chunk_index >= 0 else '0'}.parquet"

    buffer = io.BytesIO()
    df_out.write_parquet(buffer, use_pyarrow=True)
    buffer.seek(0)

    s3_client.put_object(
        Bucket=SIM_BUCKET,
        Key=s3_key,
        Body=buffer.getvalue(),
    )

    logger.info(f"✅ Upload batch ({df_out.height} dòng, {df_out['Symbol'].n_unique()} tickers) → s3://{SIM_BUCKET}/{s3_key}")
    return [s3_key]


def _process_sqs_record(body: dict) -> dict:
    """
    Xử lý 1 SQS record: load data → filter → upload.
    Trả về dict tóm tắt kết quả.
    """
    trade_date: str = body["trade_date"]
    tickers: list[str] = body["tickers"]
    chunk_index: int = body.get("chunk_index", -1)
    total_chunks: int = body.get("total_chunks", -1)

    logger.info(
        f"📦 Chunk {chunk_index+1}/{total_chunks} | "
        f"trade_date={trade_date} | {len(tickers)} tickers"
    )

    # Xác định năm để đọc đúng file parquet
    year = datetime.strptime(trade_date, "%Y-%m-%d").year

    # Đọc (hoặc lấy từ cache) file năm
    year_df = load_year_from_s3(year)

    # Filter theo ngày và tickers của chunk này
    df_day = filter_day_and_tickers(year_df, trade_date, tickers)

    if df_day.height == 0:
        logger.warning(
            f"Không có data cho trade_date={trade_date} "
            f"với {len(tickers)} tickers của chunk này. "
            f"(Có thể ngày lễ hoặc tickers không có trong processed/)"
        )
        return {
            "trade_date": trade_date,
            "chunk_index": chunk_index,
            "uploaded": 0,
            "skipped_tickers": tickers,
        }

    # Upload gộp theo chunk (thay vì 1 file per ticker)
    uploaded_keys = upload_chunk_to_sim(df_day, trade_date, chunk_index)

    return {
        "trade_date": trade_date,
        "chunk_index": chunk_index,
        "uploaded": df_day["Symbol"].n_unique(),
        "skipped_tickers": list(set(tickers) - set(df_day["Symbol"].to_list())),
    }

# Lambda Handler
def lambda_handler(event, context):
    """
    [Replay Consumer]
    Triggered bởi SQS (fan-out từ lambda_replay_producer).
    Xử lý Partial Batch Failure: chỉ retry đúng những record bị lỗi.
    """
    records = event.get("Records", [])
    logger.info(f"📥 Consumer nhận {len(records)} SQS record(s).")

    batch_item_failures = []

    for record in records:
        message_id = record.get("messageId", "unknown")
        try:
            body = json.loads(record["body"])
            result = _process_sqs_record(body)
            logger.info(
                f"🎉 Record {message_id[:8]}: "
                f"{result['uploaded']} uploaded, "
                f"{len(result.get('skipped_tickers', []))} skipped"
            )

        except Exception as e:
            logger.error(f"❌ Lỗi record {message_id}: {str(e)}", exc_info=True)
            batch_item_failures.append({"itemIdentifier": message_id})

    if batch_item_failures:
        logger.warning(f"⚠️ {len(batch_item_failures)} record(s) thất bại — SQS sẽ retry.")

    return {"batchItemFailures": batch_item_failures}

# Local test runner
if __name__ == "__main__":
    import argparse
    import sys
    import os

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

    parser = argparse.ArgumentParser(description="Local test runner cho Replay Consumer")
    parser.add_argument("--date", type=str, required=True, help="Ngày replay (YYYY-MM-DD)")
    parser.add_argument(
        "--tickers",
        type=str,
        default="AAPL,MSFT,GOOGL,AMZN,NVDA",
        help="Danh sách tickers test (cách nhau bởi dấu phẩy)",
    )
    args = parser.parse_args()

    test_tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]

    mock_event = {
        "Records": [
            {
                "messageId": "test-replay-consumer-001",
                "receiptHandle": "mock",
                "body": json.dumps({
                    "trade_date": args.date,
                    "tickers": test_tickers,
                    "chunk_index": 0,
                    "total_chunks": 1,
                }),
                "attributes": {},
                "messageAttributes": {},
                "md5OfBody": "",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:ap-southeast-1:000000000000:replay-queue",
                "awsRegion": "ap-southeast-1",
            }
        ]
    }

    print(f"=== MOCK REPLAY EVENT ===")
    print(f"  trade_date : {args.date}")
    print(f"  tickers    : {test_tickers}")
    print()

    result = lambda_handler(mock_event, None)
    print("\n=== KẾT QUẢ ===")
    print(result)
