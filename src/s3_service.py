import io
import boto3
import polars as pl
from logger import get_logger

logger = get_logger(__name__)
s3_client = boto3.client('s3')

def read_parquet_from_s3(bucket: str, key: str) -> pl.DataFrame:
    """Đọc file Parquet từ S3 và trả về Polars DataFrame."""
    logger.info(f"Đang đọc dữ liệu từ s3://{bucket}/{key}")
    response = s3_client.get_object(Bucket=bucket, Key=key)
    parquet_bytes = response['Body'].read()
    return pl.read_parquet(io.BytesIO(parquet_bytes))

def write_parquet_to_s3(df: pl.DataFrame, bucket: str, key: str) -> None:
    """Ghi Polars DataFrame lên S3 dưới dạng Parquet (Dùng cho Processed và Quarantine)."""
    logger.info(f"Đang upload file Parquet lên s3://{bucket}/{key}")
    buffer = io.BytesIO()
    df.write_parquet(buffer, use_pyarrow=True)
    buffer.seek(0)
    
    s3_client.put_object(
        Bucket=bucket, 
        Key=key, 
        Body=buffer.getvalue()
    )

def write_csv_to_s3(df: pl.DataFrame, bucket: str, key: str) -> None:
    """Ghi Polars DataFrame lên S3 dưới dạng CSV (Dùng cho Report)."""
    logger.info(f"Đang upload file CSV Report lên s3://{bucket}/{key}")
    buffer = io.BytesIO()
    df.write_csv(buffer)
    buffer.seek(0)
    
    s3_client.put_object(
        Bucket=bucket, 
        Key=key, 
        Body=buffer.getvalue()
    )

def list_parquet_files_in_s3(bucket: str, prefix: str) -> list[str]:
    """Quét và trả về danh sách các object key (.parquet) trong một thư mục S3."""
    logger.info(f"Đang quét danh sách file tại s3://{bucket}/{prefix}")
    keys = []
    
    # Dùng Paginator để quét nếu số lượng file > 1000
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket, Prefix=prefix)
    
    for page in pages:
        if 'Contents' in page:
            for obj in page['Contents']:
                if obj['Key'].endswith('.parquet'):
                    keys.append(obj['Key'])
    return keys