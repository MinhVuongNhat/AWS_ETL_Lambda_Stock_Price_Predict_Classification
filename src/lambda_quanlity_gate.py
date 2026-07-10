import os
import urllib.parse
import polars as pl
from config import CLEANSED_BUCKET, CLEANSED_PREFIX, QUARANTINE_BUCKET, QUARANTINE_PREFIX, PROCESSED_BUCKET
from logger import get_logger

from s3_service import read_parquet_from_s3, write_parquet_to_s3, write_csv_to_s3
from cleaning import clean_data
from validator import validate_data, verify_clean_schema_contract
from quarantine import split_valid_invalid
from report import generate_quality_report

logger = get_logger(__name__)
REPORT_PREFIX = os.environ.get('REPORT_PREFIX', 'reports/')

def lambda_handler(event, context):
    """Triggered khi 1 file thô (Raw) được upload."""
    try:
        record = event['Records'][0]
        source_bucket = record['s3']['bucket']['name']
        source_key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        filename = source_key.split('/')[-1]
        
        if not source_key.endswith('.parquet'):
            return {'statusCode': 200, 'body': 'Skipped'}

        # 1. EXTRACT
        raw_df = read_parquet_from_s3(source_bucket, source_key)
        original_rows = raw_df.height
        
        # 2. CLEAN & VALIDATE
        cleaned_df, duplicate_count = clean_data(raw_df)
        validated_df = validate_data(cleaned_df)
        
        # 3. QUARANTINE SPLIT
        clean_df, quarantine_df = split_valid_invalid(validated_df)
        
        # 4. REPORT (Lưu lên S3)
        metrics = generate_quality_report(validated_df, original_rows, duplicate_count, filename)
        report_df = pl.DataFrame([metrics])
        write_csv_to_s3(report_df, PROCESSED_BUCKET, f"{REPORT_PREFIX}report_{filename.replace('.parquet', '')}.csv")

        # 5. LƯU DỮ LIỆU SẠCH (Vào vùng đệm Cleansed - KHÔNG biến đổi Feature)
        if clean_df.height > 0:
            final_clean_df = verify_clean_schema_contract(clean_df) # Chốt chặn Schema
            write_parquet_to_s3(final_clean_df, CLEANSED_BUCKET, f"{CLEANSED_PREFIX}{filename}")
            
        # 6. LƯU DỮ LIỆU LỖI
        if quarantine_df.height > 0:
            write_parquet_to_s3(quarantine_df, QUARANTINE_BUCKET, f"{QUARANTINE_PREFIX}error_{filename}")

        return {'statusCode': 200, 'body': f'Quality Gate Passed: {filename}'}

    except Exception as e:
        logger.error(f"Lỗi hệ thống tại Quality Gate: {str(e)}")
        raise e