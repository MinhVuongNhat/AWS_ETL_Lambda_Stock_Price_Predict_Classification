import polars as pl
from datetime import datetime, timezone

import boto3

from config import (
    CLEANSED_BUCKET,
    CLEANSED_DAILY_PREFIX,
    PROCESSED_BUCKET,
    PROCESSED_PREFIX,
    SOURCE_PROCESSED_BUCKET,
)
from logger import get_logger
from s3_service import (
    list_parquet_files_in_s3,
    read_parquet_from_s3,
    write_parquet_to_s3,
    delete_s3_objects,
)
from transform import apply_incremental_transform

logger = get_logger(__name__)

s3_client = boto3.client("s3")


def list_pending_dates(cleansed_bucket: str, cleansed_daily_prefix: str) -> list[str]:
    """
    Quét S3 để tìm tất cả các ngày đang có dữ liệu trong cleansed_daily/.
    Trả về danh sách date string (YYYY-MM-DD) đã sắp xếp tăng dần.
    """
    paginator = s3_client.get_paginator("list_objects_v2")
    pages = paginator.paginate(
        Bucket=cleansed_bucket,
        Prefix=cleansed_daily_prefix,
        Delimiter="/",
    )

    pending_dates = []
    for page in pages:
        for cp in page.get("CommonPrefixes", []):
            # cp["Prefix"] = "cleansed_daily/2025-01-02/"
            date_str = cp["Prefix"].rstrip("/").split("/")[-1]
            # Validate format YYYY-MM-DD
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                pending_dates.append(date_str)
            except ValueError:
                logger.warning(f"Bỏ qua prefix không hợp lệ: {cp['Prefix']}")

    return sorted(pending_dates)


def process_one_date(trade_date: str) -> dict:
    """
    Xử lý ETL cho một ngày giao dịch cụ thể.
    Merge data ngày đó vào file năm trong PROCESSED_BUCKET.
    Trả về dict tóm tắt kết quả.
    """
    logger.info(f"\n{'─'*60}")
    logger.info(f"ETL: Đang xử lý ngày {trade_date}...")

    current_year = datetime.strptime(trade_date, "%Y-%m-%d").year

    # Bước 1: Quét vùng đệm cleansed_daily/{trade_date}/
    daily_prefix = f"{CLEANSED_DAILY_PREFIX}{trade_date}/"
    cleansed_keys = list_parquet_files_in_s3(CLEANSED_BUCKET, daily_prefix)

    if not cleansed_keys:
        logger.warning(
            f"Không có dữ liệu tại s3://{CLEANSED_BUCKET}/{daily_prefix}. "
            f"Bỏ qua ngày này."
        )
        return {"trade_date": trade_date, "status": "no_data", "rows_merged": 0}

    logger.info(f"Tìm thấy {len(cleansed_keys)} file sạch cho ngày {trade_date}.")

    # Bước 2: Đọc và gom dữ liệu ngày mới
    daily_df_list = [read_parquet_from_s3(CLEANSED_BUCKET, key) for key in cleansed_keys]
    new_daily_df = pl.concat(daily_df_list, how="diagonal_relaxed")
    logger.info(f"Tổng dữ liệu ngày mới: {new_daily_df.height} dòng.")

    # Bước 3: Tải file năm từ SOURCE_PROCESSED_BUCKET làm historical context.
    # SOURCE_PROCESSED_BUCKET mặc định = PROCESSED_BUCKET (production).
    # Khi chạy replay, SOURCE_PROCESSED_BUCKET = production bucket (có data backfill)
    # còn PROCESSED_BUCKET = SIM_BUCKET (nơi ghi kết quả replay).
    year_key = f"{PROCESSED_PREFIX}{current_year}.parquet"
    logger.info(f"Tải Historical Context từ: s3://{SOURCE_PROCESSED_BUCKET}/{year_key}")
    try:
        year_df = read_parquet_from_s3(SOURCE_PROCESSED_BUCKET, year_key)
        logger.info(f"Historical Context: {year_df.height} dòng.")
    except Exception as e:
        if "NoSuchKey" in str(e) or "404" in str(e):
            logger.warning(
                f"File {year_key} chưa tồn tại tại s3://{SOURCE_PROCESSED_BUCKET}/. "
                f"Khởi tạo dataset mới từ đầu (first run)."
            )
            year_df = pl.DataFrame()
        else:
            raise

    # Bước 4: Merge & Recalculate Feature Engineering
    updated_year_df = apply_incremental_transform(year_df, new_daily_df)

    # Bước 5: Ghi đè file năm lên PROCESSED_BUCKET
    logger.info(f"Ghi đè s3://{PROCESSED_BUCKET}/{year_key} ({updated_year_df.height} dòng)...")
    write_parquet_to_s3(updated_year_df, PROCESSED_BUCKET, year_key)
    logger.info(f"✅ Đã cập nhật: s3://{PROCESSED_BUCKET}/{year_key}")

    # Bước 6: Dọn dẹp vùng đệm
    logger.info(f"Dọn dẹp {len(cleansed_keys)} file trong {daily_prefix}...")
    delete_s3_objects(CLEANSED_BUCKET, cleansed_keys)

    logger.info(f"🎉 ETL hoàn tất cho ngày {trade_date}: {new_daily_df.height} dòng merged.")
    return {
        "trade_date": trade_date,
        "status": "success",
        "rows_merged": new_daily_df.height,
        "year_key": year_key,
    }


def lambda_handler(event, context):
    """
    [Pipeline B - Daily Increment ETL]
    Scan toàn bộ cleansed_daily/ để tìm và xử lý TẤT CẢ các ngày đang chờ,
    đảm bảo hoạt động đúng cả trong production lẫn replay mode.
    """
    try:
        logger.info("🚀 KHỞI ĐỘNG DAILY INCREMENT ETL JOB...")
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        logger.info(f"Thời điểm chạy (UTC): {now_utc}")

        # Bước 1: Tìm tất cả ngày đang chờ xử lý
        pending_dates = list_pending_dates(CLEANSED_BUCKET, CLEANSED_DAILY_PREFIX)

        if not pending_dates:
            logger.info(
                f"Không có ngày nào đang chờ trong "
                f"s3://{CLEANSED_BUCKET}/{CLEANSED_DAILY_PREFIX}. "
                f"No-op."
            )
            return {"statusCode": 200, "body": "No-op: no pending dates", "processed": []}

        logger.info(f"Tìm thấy {len(pending_dates)} ngày đang chờ: {pending_dates}")

        # Bước 2: Xử lý từng ngày theo thứ tự tăng dần
        results = []
        for trade_date in pending_dates:
            try:
                result = process_one_date(trade_date)
                results.append(result)
            except Exception as e:
                logger.error(f"❌ ETL thất bại cho ngày {trade_date}: {str(e)}", exc_info=True)
                results.append({
                    "trade_date": trade_date,
                    "status": "error",
                    "error": str(e),
                })

        # Tóm tắt
        success_count = sum(1 for r in results if r.get("status") == "success")
        total_rows = sum(r.get("rows_merged", 0) for r in results)
        logger.info(
            f"\n🎉 ETL HOÀN TẤT: {success_count}/{len(pending_dates)} ngày thành công | "
            f"{total_rows} dòng đã merge."
        )

        return {
            "statusCode": 200,
            "body": f"ETL completed: {success_count}/{len(pending_dates)} dates processed",
            "processed": results,
        }

    except Exception as e:
        logger.error(f"❌ Lỗi nghiêm trọng tại Daily Increment ETL: {str(e)}", exc_info=True)
        raise
