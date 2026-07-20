import io
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

import boto3
import polars as pl
import yfinance as yf

from config import (
    RAW_BUCKET,
    RAW_PREFIX,
    TICKERS_CONFIG_BUCKET,
    TICKERS_S3_KEY,
)
from logger import get_logger

# Số lần retry tối đa cho 1 ticker trước khi bỏ qua
_MAX_TICKER_RETRIES = 1

logger = get_logger(__name__)

s3_client = boto3.client("s3")

# Helper: Tải danh sách ticker từ S3
def load_tickers_from_s3() -> list[str]:
    """
    Đọc file JSON trên S3 và trả về danh sách ticker.
    Format JSON: {"tickers": ["AAPL", "MSFT", ...]}
    """
    logger.info(f"Đang tải danh sách ticker từ s3://{TICKERS_CONFIG_BUCKET}/{TICKERS_S3_KEY}")
    response = s3_client.get_object(Bucket=TICKERS_CONFIG_BUCKET, Key=TICKERS_S3_KEY)
    content = response["Body"].read().decode("utf-8")
    data = json.loads(content)
    tickers = data.get("tickers", [])
    if not tickers:
        raise ValueError(f"Danh sách ticker rỗng trong s3://{TICKERS_CONFIG_BUCKET}/{TICKERS_S3_KEY}")
    logger.info(f"Đã tải {len(tickers)} ticker: {tickers[:5]}{'...' if len(tickers) > 5 else ''}")
    return tickers

# Helper: Tải dữ liệu từ yfinance
def fetch_daily_data(ticker: str, trade_date: str) -> Optional[pl.DataFrame]:
    """
    Tải dữ liệu OHLCV cho một ticker vào ngày giao dịch trade_date (YYYY-MM-DD).
    Dùng period end = trade_date + 1 ngày để bao gồm đúng ngày cần.
    Trả về None nếu không có dữ liệu (ngày nghỉ / ticker lỗi).
    """
    # yfinance cần [start, end) – end là ngày kế tiếp
    trade_date_obj = datetime.strptime(trade_date, "%Y-%m-%d").date()
    end_date = (trade_date_obj + timedelta(days=1)).strftime("%Y-%m-%d")

    logger.info(f"  [{ticker}] Tải dữ liệu ngày {trade_date} từ yfinance...")
    raw = yf.download(
        tickers=ticker,
        start=trade_date,
        end=end_date,
        auto_adjust=False,   # Giữ cả 'Close' và 'Adj Close'
        progress=False,
        threads=False,
    )

    if raw is None or raw.empty:
        logger.warning(f"  [{ticker}] Không có dữ liệu cho ngày {trade_date} (thị trường nghỉ?)")
        return None

    # Flatten MultiIndex nếu có (xảy ra khi download nhiều ticker)
    if isinstance(raw.columns, type(raw.columns)) and hasattr(raw.columns, "levels"):
        raw.columns = [col[0] if isinstance(col, tuple) else col for col in raw.columns]

    # Reset index để 'Date' trở thành cột thường
    raw = raw.reset_index()

    # Chuyển sang Polars
    df = pl.from_pandas(raw)

    # Chuẩn hóa tên cột: yfinance trả về "Datetime" hoặc "Date"
    if "Datetime" in df.columns:
        df = df.rename({"Datetime": "Date"})

    # Đảm bảo cột Date là kiểu pl.Date
    if df["Date"].dtype != pl.Date:
        df = df.with_columns(pl.col("Date").cast(pl.Date))

    # Giữ lại đúng những cột schema yêu cầu
    required_cols = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
    available_cols = [c for c in required_cols if c in df.columns]
    df = df.select(available_cols)

    # Thêm cột Symbol, Year, Asset_Type theo schema
    df = df.with_columns([
        pl.lit(ticker).alias("Symbol"),
        pl.col("Date").dt.year().cast(pl.Int64).alias("Year"),
        pl.lit("Stock").alias("Asset_Type"),
    ])

    # Ép kiểu các cột giá về Float64 và Volume về Int64
    price_cols = ["Open", "High", "Low", "Close", "Adj Close"]
    for col in price_cols:
        if col in df.columns:
            df = df.with_columns(pl.col(col).cast(pl.Float64))
    if "Volume" in df.columns:
        df = df.with_columns(pl.col("Volume").cast(pl.Int64))

    logger.info(f"  [{ticker}] Tải thành công: {df.height} dòng.")
    return df

# Helper: Upload DataFrame lên S3 dưới dạng Parquet
def upload_df_to_s3_raw(df: pl.DataFrame, ticker: str, trade_date: str) -> str:
    """
    Ghi DataFrame thành Parquet và upload lên s3://RAW_BUCKET/raw/YYYY-MM-DD/TICKER.parquet
    Trả về S3 key đã upload.
    """
    s3_key = f"{RAW_PREFIX}{trade_date}/{ticker}.parquet"
    buffer = io.BytesIO()
    df.write_parquet(buffer, use_pyarrow=True)
    buffer.seek(0)

    s3_client.put_object(
        Bucket=RAW_BUCKET,
        Key=s3_key,
        Body=buffer.getvalue(),
    )
    logger.info(f"  [{ticker}] ✅ Đã upload: s3://{RAW_BUCKET}/{s3_key}")
    return s3_key

# Lambda Handler
def _process_batch(tickers: list[str], trade_date: str) -> dict:
    """
    Xử lý một batch tickers: download từ yfinance và upload lên S3.
    Trả về dict tổng kết: {uploaded, skipped, failed_tickers}
    Không raise exception - lỗi của từng ticker được log và ghi vào failed_tickers.
    """
    uploaded_keys = []
    skipped_tickers = []
    failed_tickers = []

    for ticker in tickers:
        try:
            df = fetch_daily_data(ticker, trade_date)
            if df is None or df.height == 0:
                skipped_tickers.append(ticker)
                continue
            s3_key = upload_df_to_s3_raw(df, ticker, trade_date)
            uploaded_keys.append(s3_key)
        except Exception as e:
            logger.error(f"  [{ticker}] ❌ Lỗi: {str(e)}")
            failed_tickers.append(ticker)

    return {
        "uploaded": len(uploaded_keys),
        "skipped": len(skipped_tickers),
        "failed_tickers": failed_tickers,
    }


def lambda_handler(event, context):
    """
    [Pipeline B - Daily Collector - Consumer]
    Triggered bởi SQS (Fan-out pattern từ lambda_collector_producer).
    """
    logger.info(f"📥 Consumer nhận event với {len(event.get('Records', []))} SQS record(s).")

    # Partial Batch Failure: thu thập các messageId bị lỗi
    batch_item_failures = []

    for record in event.get("Records", []):
        message_id = record.get("messageId", "unknown")
        try:
            # Parse SQS message body
            body = json.loads(record["body"])
            trade_date: str = body["trade_date"]
            tickers: list[str] = body["tickers"]
            chunk_index: int = body.get("chunk_index", -1)
            total_chunks: int = body.get("total_chunks", -1)

            logger.info(
                f"🚀 Bắt đầu xử lý chunk {chunk_index + 1}/{total_chunks} "
                f"| trade_date={trade_date} | {len(tickers)} tickers "
                f"| messageId={message_id[:8]}..."
            )

            # Xử lý batch tickers
            result = _process_batch(tickers, trade_date)

            summary = (
                f"Chunk {chunk_index + 1}/{total_chunks} hoàn tất "
                f"[{trade_date}]: "
                f"{result['uploaded']} uploaded | "
                f"{result['skipped']} skipped | "
                f"{len(result['failed_tickers'])} failed"
            )
            logger.info(f"🎉 {summary}")
            if result["failed_tickers"]:
                logger.warning(f"  Failed tickers trong chunk này: {result['failed_tickers']}")

        except Exception as e:
            # Lỗi nghiêm trọng (parse JSON thất bại, thiếu key...)
            logger.error(
                f"❌ Lỗi nghiêm trọng khi xử lý record messageId={message_id}: {str(e)}"
            )
            batch_item_failures.append({"itemIdentifier": message_id})

    # Trả về partial batch failure (SQS chỉ retry đúng những message bị lỗi)
    if batch_item_failures:
        logger.warning(
            f"⚠️ {len(batch_item_failures)} record(s) thất bại – SQS sẽ retry."
        )
        return {"batchItemFailures": batch_item_failures}

    return {"batchItemFailures": []}

# Local test runner
if __name__ == "__main__":
    import argparse
    import os
    import sys

    # Cho phép chạy local mà không cần PYTHONPATH
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

    parser = argparse.ArgumentParser(description="Local test runner cho Daily Collector Consumer")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Chạy lambda_handler với mock SQS event để kiểm tra local",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Override ngày giao dịch (YYYY-MM-DD). Mặc định: hôm qua.",
    )
    parser.add_argument(
        "--tickers",
        type=str,
        default="AAPL,MSFT,GOOGL",
        help="Danh sách tickers test cách nhau bởi dấu phẩy (mặc định: AAPL,MSFT,GOOGL).",
    )
    args = parser.parse_args()

    if args.test:
        # Xác định trade_date
        if args.date:
            trade_date_local = args.date
        else:
            trade_date_local = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

        # Tickers test
        test_tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]

        # Tạo mock SQS event (giống event thật AWS gửi)
        mock_sqs_event = {
            "Records": [
                {
                    "messageId": "test-message-id-00000001",
                    "receiptHandle": "mock-receipt-handle",
                    "body": json.dumps({
                        "trade_date": trade_date_local,
                        "tickers": test_tickers,
                        "chunk_index": 0,
                        "total_chunks": 1,
                    }),
                    "attributes": {},
                    "messageAttributes": {},
                    "md5OfBody": "",
                    "eventSource": "aws:sqs",
                    "eventSourceARN": "arn:aws:sqs:ap-southeast-1:000000000000:daily-collector-queue",
                    "awsRegion": "ap-southeast-1",
                }
            ]
        }

        print(f"=== MOCK SQS EVENT ===")
        print(f"  trade_date : {trade_date_local}")
        print(f"  tickers    : {test_tickers}")
        print()

        result = lambda_handler(mock_sqs_event, None)
        print("\n=== KẾT QUẢ ===")
        print(result)
