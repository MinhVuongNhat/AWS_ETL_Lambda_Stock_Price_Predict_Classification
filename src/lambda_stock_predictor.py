import io
import json
import logging
import os
from datetime import datetime
from decimal import Decimal

import boto3
import polars as pl
import xgboost as xgb
from botocore.config import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("stock_predictor")

PROCESSED_BUCKET = os.environ.get("PROCESSED_BUCKET", "my-nasdaq-stock-processed-2026-430970051812-ap-southeast-1-an")
MODEL_BUCKET     = os.environ.get("MODEL_BUCKET",     "my-nasdaq-stock-models-2026-430970051812-ap-southeast-1-an")
MODEL_PREFIX     = os.environ.get("MODEL_PREFIX",     "models/xgboost_v1/")
DYNAMODB_TABLE   = os.environ.get("DYNAMODB_TABLE",   "NasdaqStockPredictions")
REGION           = os.environ.get("AWS_REGION",       "ap-southeast-1")

boto_cfg  = Config(retries={"max_attempts": 3, "mode": "adaptive"})
s3_client = boto3.client("s3", config=boto_cfg)
dynamodb  = boto3.resource("dynamodb", region_name=REGION)
table     = dynamodb.Table(DYNAMODB_TABLE)

_model_cache         = None
_feature_names_cache = None


# Model Loading

def load_model():
    global _model_cache, _feature_names_cache
    if _model_cache is not None:
        logger.info("✅ Dùng model từ Lambda cache.")
        return _model_cache, _feature_names_cache

    logger.info(f"Tải model từ s3://{MODEL_BUCKET}/{MODEL_PREFIX}...")
    resp = s3_client.get_object(Bucket=MODEL_BUCKET, Key=f"{MODEL_PREFIX}feature_names.json")
    _feature_names_cache = json.loads(resp["Body"].read())

    local_path = "/tmp/xgboost_model.json"
    s3_client.download_file(MODEL_BUCKET, f"{MODEL_PREFIX}model.json", local_path)
    _model_cache = xgb.Booster()
    _model_cache.load_model(local_path)
    logger.info("✅ Tải model thành công.")
    return _model_cache, _feature_names_cache


# S3 Helpers

def read_json_s3(bucket: str, key: str) -> dict | list | None:
    try:
        resp = s3_client.get_object(Bucket=bucket, Key=key)
        return json.loads(resp["Body"].read().decode("utf-8"))
    except s3_client.exceptions.NoSuchKey:
        return None
    except Exception:
        return None


def write_json_s3(bucket: str, key: str, data):
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(data, ensure_ascii=False),
        ContentType="application/json"
    )
    logger.info(f"  ✓ s3://{bucket}/{key}")


# DynamoDB

def write_to_dynamodb(records: list[dict], date_str: str):
    logger.info(f"Ghi {len(records)} bản ghi vào DynamoDB...")
    with table.batch_writer() as batch:
        for rec in records:
            batch.put_item(Item={
                "Symbol":      rec["Symbol"],
                "Date":        date_str,
                "Prediction":  int(rec["Prediction"]),
                "Probability": Decimal(str(round(float(rec["Probability"]), 6))),
                "LatestFlag":  1,
                "UpdatedAt":   datetime.utcnow().isoformat() + "Z"
            })
    logger.info("✅ DynamoDB ghi xong.")


# S3 Data Files

def write_daily_all(records: list[dict], date_str: str):
    """Ghi toàn bộ dự đoán ngày hôm nay ra S3"""
    write_json_s3(PROCESSED_BUCKET, f"predictions/{date_str}/all.json", records)


def write_latest_summary(records: list[dict], date_str: str):
    """Ghi file latest.json với top10/bottom10 cho Dashboard"""
    sorted_asc  = sorted(records, key=lambda r: r["Probability"])
    sorted_desc = sorted(records, key=lambda r: r["Probability"], reverse=True)

    top10    = sorted_desc[:10]
    bottom10 = sorted_asc[:10]
    bull_cnt = sum(1 for r in records if r["Prediction"] == 1)

    summary = {
        "date":          date_str,
        "total":         len(records),
        "bullish_count": bull_cnt,
        "bearish_count": len(records) - bull_cnt,
        "bullish_pct":   round(bull_cnt / len(records) * 100, 1) if records else 0,
        "top10":         top10,
        "bottom10":      bottom10,
        "updated_at":    datetime.utcnow().isoformat() + "Z"
    }
    write_json_s3(PROCESSED_BUCKET, "predictions/latest.json", summary)


def update_symbol_history(records: list[dict], date_str: str):
    """
    Tối ưu hóa chi phí: API Handler đọc lịch sử trực tiếp từ DynamoDB.
    Hàm này giữ lại để lưu file backup tổng hợp 1 file duy nhất thay vì 3,000 file riêng lẻ.
    """
    logger.info(f"Ghi nhận lịch sử tổng hợp ngày {date_str} ({len(records)} symbols)...")
    key = f"predictions/{date_str}/history_summary.json"
    write_json_s3(PROCESSED_BUCKET, key, records)
    logger.info("✅ Cập nhật lịch sử tổng hợp xong (1 S3 PUT request).")


# Lambda Handler

def lambda_handler(event, context):
    try:
        if "Records" not in event:
            return {"statusCode": 400, "body": "No S3 event records"}

        record        = event["Records"][0]
        source_bucket = record["s3"]["bucket"]["name"]
        source_key    = record["s3"]["object"]["key"]
        logger.info(f"Triggered: s3://{source_bucket}/{source_key}")

        model, feature_names = load_model()

        # Đọc parquet
        resp = s3_client.get_object(Bucket=source_bucket, Key=source_key)
        df   = pl.read_parquet(io.BytesIO(resp["Body"].read()))

        if df.height == 0:
            return {"statusCode": 200, "body": "Empty parquet, skipping."}

        latest_date = str(df["Date"].max())[:10]
        logger.info(f"Ngày mới nhất: {latest_date}")

        df_latest = df.filter(pl.col("Date").cast(pl.Utf8).str.starts_with(latest_date))
        df_clean  = df_latest.drop_nulls(subset=feature_names)

        if df_clean.height == 0:
            return {"statusCode": 200, "body": "No valid data for prediction"}

        # Predict
        X       = df_clean.select(feature_names).to_pandas()
        dmatrix = xgb.DMatrix(X)
        y_prob  = model.predict(dmatrix)
        y_pred  = (y_prob >= 0.5).astype(int)

        df_result = df_clean.select(["Symbol"]).with_columns([
            pl.Series("Prediction",  y_pred, dtype=pl.Int8),
            pl.Series("Probability", [round(float(p), 6) for p in y_prob], dtype=pl.Float64)
        ]).sort("Probability", descending=True)

        records = df_result.to_dicts()

        # Ghi vào các destinations (Tối ưu hóa: chỉ tốn 3 S3 PUT + 1 DynamoDB batch write)
        logger.info("Bắt đầu ghi output...")
        write_daily_all(records, latest_date)
        write_latest_summary(records, latest_date)
        update_symbol_history(records, latest_date)
        write_to_dynamodb(records, latest_date)

        logger.info(f"✅ Hoàn tất: {len(records)} mã cho ngày {latest_date}.")
        return {"statusCode": 200, "body": f"Predicted {len(records)} tickers for {latest_date}"}

    except Exception as e:
        logger.error(f"❌ Lỗi: {e}", exc_info=True)
        raise
