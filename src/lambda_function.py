import os
import urllib.parse
import polars as pl
from config import PROCESSED_BUCKET, PROCESSED_PREFIX, QUARANTINE_BUCKET, QUARANTINE_PREFIX
from logger import get_logger

# Import các Module nghiệp vụ (Single Responsibility)
from s3_service import read_parquet_from_s3, write_parquet_to_s3, write_csv_to_s3
from cleaning import clean_data
from validator import validate_data, verify_clean_schema_contract
from quarantine import split_valid_invalid
from report import generate_quality_report
from transform import transform_pipeline

logger = get_logger(__name__)

# Thêm prefix cho Report (nếu chưa có trong config.py)
REPORT_PREFIX = os.environ.get('REPORT_PREFIX', 'reports/')

def lambda_handler(event, context):
    try:
        # Lấy thông tin file từ Event S3 trigger
        record = event['Records'][0]
        source_bucket = record['s3']['bucket']['name']
        source_key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        filename = source_key.split('/')[-1] # Ví dụ: AAPL.parquet
        symbol_name = filename.replace('.parquet', '')
        
        if not source_key.endswith('.parquet'):
            return {'statusCode': 200, 'body': 'Skipped non-parquet file'}

        logger.info(f"🚀 BẮT ĐẦU PIPELINE CHO MÃ: {symbol_name}")

        # 1. EXTRACT: Đọc dữ liệu nguyên bản
        raw_df = read_parquet_from_s3(source_bucket, source_key)
        original_rows = raw_df.height
        
        # 2. CLEAN: Dọn dẹp lỗi kỹ thuật & ép kiểu
        cleaned_df, duplicate_count = clean_data(raw_df)
        
        # 3. VALIDATE: Quét luật nghiệp vụ và gán cờ 'invalid_reason'
        validated_df = validate_data(cleaned_df)
        
        # 4. QUARANTINE: Bóc tách luồng Sạch và Lỗi
        clean_df, quarantine_df = split_valid_invalid(validated_df)
        
        # 5. REPORT: Thu thập thống kê & Lưu báo cáo lên S3
        metrics = generate_quality_report(validated_df, original_rows, duplicate_count, filename)
        
        # In log tổng quát để CloudWatch ghi nhận
        logger.info(f"📊 REPORT [{symbol_name}]: Input={metrics['Original_Rows']} | Clean={metrics['Clean_Processed_Rows']} | Quarantine={metrics['Total_Quarantined']}")
        
        report_df = pl.DataFrame([metrics])
        write_csv_to_s3(report_df, PROCESSED_BUCKET, f"{REPORT_PREFIX}report_{symbol_name}.csv")

        # 6. TRANSFORM & LOAD DỮ LIỆU SẠCH
        if clean_df.height > 0:
            # 6a. Chốt chặn Schema Contract
            final_clean_df = verify_clean_schema_contract(clean_df)
            
            # 6b. Feature Engineering & Partitioning (Chia năm)
            partitioned_data = transform_pipeline(final_clean_df)
            
            # 6c. Upload các phân mảnh lên S3 (Định dạng HIVE: year=2024/AAPL.parquet)
            for year, part_df in partitioned_data.items():
                part_key = f"{PROCESSED_PREFIX}year={year}/{filename}"
                write_parquet_to_s3(part_df, PROCESSED_BUCKET, part_key)
            
        # 7. LOAD DỮ LIỆU CÁCH LY
        if quarantine_df.height > 0:
            write_parquet_to_s3(
                df=quarantine_df,
                bucket=QUARANTINE_BUCKET,
                key=f"{QUARANTINE_PREFIX}error_{filename}"
            )

        logger.info(f"✅ Hoàn tất toàn bộ chu trình ETL cho {symbol_name}.")
        return {'statusCode': 200, 'body': f'ETL Completed for {filename}'}

    except Exception as e:
        logger.error(f"❌ Pipeline thất bại dữ dội: {str(e)}")
        raise e