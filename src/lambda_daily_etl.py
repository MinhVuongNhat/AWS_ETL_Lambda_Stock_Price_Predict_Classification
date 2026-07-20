"""
[Pipeline B - Daily Increment ETL]
Lambda function được EventBridge kích hoạt lúc cuối ngày giao dịch (vd: 00:00 UTC hàng ngày).
"""
import polars as pl
from datetime import datetime, timezone

from config import (
    CLEANSED_BUCKET,
    CLEANSED_DAILY_PREFIX,
    PROCESSED_BUCKET,
    PROCESSED_PREFIX,
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


def lambda_handler(event, context):
    """
    [Pipeline B - Daily Increment]
    Triggered bởi EventBridge Scheduler lúc cuối ngày giao dịch.
    """
    try:
        logger.info("🚀 KHỞI ĐỘNG DAILY INCREMENT ETL JOB...")

        # Bước 1: Xác định ngày và năm xử lý
        now_utc = datetime.now(timezone.utc)
        today_str = now_utc.strftime('%Y-%m-%d')
        current_year = now_utc.year
        logger.info(f"Ngày xử lý: {today_str} | Năm hiện tại: {current_year}")

        # Bước 2: Quét vùng đệm cleansed_daily/{today}/
        daily_prefix = f"{CLEANSED_DAILY_PREFIX}{today_str}/"
        cleansed_keys = list_parquet_files_in_s3(CLEANSED_BUCKET, daily_prefix)

        if not cleansed_keys:
            # No-op: Thị trường đóng cửa hoặc Quality Gate chưa chạy
            logger.info(
                f"Không có dữ liệu mới tại s3://{CLEANSED_BUCKET}/{daily_prefix}. "
                f"Có thể thị trường nghỉ giao dịch hôm nay. Kết thúc Job (No-op)."
            )
            return {'statusCode': 200, 'body': f'No-op: No data for {today_str}'}

        logger.info(f"Tìm thấy {len(cleansed_keys)} file sạch cho ngày {today_str}.")

        # Bước 3: Đọc và gom toàn bộ dữ liệu ngày mới
        daily_df_list = [read_parquet_from_s3(CLEANSED_BUCKET, key) for key in cleansed_keys]
        new_daily_df = pl.concat(daily_df_list, how="diagonal_relaxed")
        logger.info(f"Tổng dữ liệu ngày mới: {new_daily_df.height} dòng.")

        # Bước 4: Tải file năm hiện tại từ S3
        year_key = f"{PROCESSED_PREFIX}{current_year}.parquet"
        logger.info(f"Đang tải Historical Context: s3://{PROCESSED_BUCKET}/{year_key}")
        year_df = read_parquet_from_s3(PROCESSED_BUCKET, year_key)
        logger.info(f"Historical Context: {year_df.height} dòng.")

        # Bước 5: Merge & Recalculate Feature Engineering
        # apply_incremental_transform xử lý: concat → deduplicate → FE → normalize
        updated_year_df = apply_incremental_transform(year_df, new_daily_df)

        # Bước 6: Ghi đè file năm lên S3
        logger.info(f"Đang ghi đè s3://{PROCESSED_BUCKET}/{year_key} ({updated_year_df.height} dòng)...")
        write_parquet_to_s3(updated_year_df, PROCESSED_BUCKET, year_key)
        logger.info(f"✅ Đã cập nhật thành công: s3://{PROCESSED_BUCKET}/{year_key}")

        # Bước 7: Dọn dẹp vùng đệm cleansed_daily/{today}/
        logger.info(f"Đang dọn dẹp {len(cleansed_keys)} file trong vùng đệm {daily_prefix}...")
        delete_s3_objects(CLEANSED_BUCKET, cleansed_keys)

        logger.info(f"🎉 HOÀN TẤT DAILY INCREMENT ETL cho ngày {today_str}.")
        return {
            'statusCode': 200,
            'body': f'Daily ETL Completed: {today_str} | {new_daily_df.height} rows merged'
        }

    except Exception as e:
        logger.error(f"❌ Lỗi nghiêm trọng tại Daily Increment ETL: {str(e)}")
        raise e
