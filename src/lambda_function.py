import urllib.parse
from config import PROCESSED_BUCKET, PROCESSED_PREFIX, QUARANTINE_BUCKET, QUARANTINE_PREFIX
from logger import get_logger
from s3_service import read_parquet_from_s3, write_parquet_to_s3
from cleaning import clean_data
from validator import validate_schema_contract

logger = get_logger(__name__)

def lambda_handler(event, context):
    try:
        # Lấy thông tin từ Event
        record = event['Records'][0]
        source_bucket = record['s3']['bucket']['name']
        source_key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        filename = source_key.split('/')[-1]
        
        if not source_key.endswith('.parquet'):
            return {'statusCode': 200, 'body': 'Skipped'}

        # 1. EXTRACT (Từ Raw)
        raw_df = read_parquet_from_s3(source_bucket, source_key)
        
        # 2. TRANSFORM (Phân tách Clean & Quarantine)
        clean_df, quarantine_df, metrics = clean_data(raw_df)
        
        # Ghi log chuẩn định dạng bạn muốn
        log_msg = (
            f"\n--- BÁO CÁO XỬ LÝ: {filename} ---\n"
            f"Input:\n{metrics['Original_Rows']} rows\n\n"
            f"Duplicate:\n{metrics['Duplicate_Dropped']}\n\n"
            f"Negative:\n{metrics['Negative_Count']}\n\n"
            f"Missing:\n{metrics['Missing_Count']}\n\n"
            f"Quarantine:\n{metrics['Quarantined_Rows']}\n\n"
            f"Output:\n{metrics['Clean_Rows']} rows\n"
            f"-----------------------------------"
        )
        logger.info(log_msg)

        # 3. CONTRACT VALIDATION (Bảo vệ Warehouse)
        if clean_df.height > 0:
            final_clean_df = validate_schema_contract(clean_df)
            
            # 4. LOAD (Ghi dữ liệu sạch)
            write_parquet_to_s3(
                df=final_clean_df, 
                bucket=PROCESSED_BUCKET, 
                key=f"{PROCESSED_PREFIX}{filename}"
            )
            
        # 4. LOAD QUARANTINE (Lưu lại file lỗi để điều tra)
        if quarantine_df.height > 0:
            write_parquet_to_s3(
                df=quarantine_df,
                bucket=QUARANTINE_BUCKET,
                key=f"{QUARANTINE_PREFIX}{filename}"
            )

        return {'statusCode': 200, 'body': 'ETL Completed Successfully'}

    except Exception as e:
        logger.error(f"Pipeline thất bại: {str(e)}")
        raise e