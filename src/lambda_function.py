import urllib.parse
from config import PROCESSED_BUCKET, PROCESSED_PREFIX
from logger import get_logger
from s3_service import read_parquet_from_s3, write_parquet_to_s3
from cleaning import clean_data, DataCleaningError
from validator import validate_data, DataValidationError

logger = get_logger(__name__)

def lambda_handler(event, context):
    logger.info("Lambda ETL Pipeline (Polars + Parquet) bắt đầu thực thi.")
    
    try:
        # Lấy thông tin file kích hoạt Lambda
        record = event['Records'][0]
        source_bucket = record['s3']['bucket']['name']
        source_key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        
        # Chỉ xử lý file có đuôi .parquet
        if not source_key.endswith('.parquet'):
            logger.warning(f"Bỏ qua file không phải parquet: {source_key}")
            return {'statusCode': 200, 'body': 'Skipped non-parquet file.'}

        # 1. EXTRACT
        raw_df = read_parquet_from_s3(bucket=source_bucket, key=source_key)
        
        # 2. TRANSFORM
        cleaned_df = clean_data(raw_df)
        validated_df = validate_data(cleaned_df)
        
        # 3. LOAD
        filename = source_key.split('/')[-1] # Lấy tên file (vd: raw_data_parquet_2026.parquet)
        processed_key = f"{PROCESSED_PREFIX}{filename}"
        
        write_parquet_to_s3(
            df=validated_df, 
            bucket=PROCESSED_BUCKET, 
            key=processed_key
        )
        
        logger.info(f"Hoàn tất xử lý: {filename}")
        return {
            'statusCode': 200, 
            'body': f'Thành công xử lý {filename}'
        }

    except (DataCleaningError, DataValidationError) as e:
        logger.error(f"Lỗi Dữ liệu/Nghiệp vụ: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Lỗi Hệ thống: {str(e)}")
        raise e