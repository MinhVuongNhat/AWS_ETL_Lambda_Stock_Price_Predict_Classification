import io
import boto3
import polars as pl
from logger import get_logger

logger = get_logger(__name__)
s3_client = boto3.client('s3')

def read_parquet_from_s3(bucket: str, key: str) -> pl.DataFrame:
    """Đọc trực tiếp file Parquet từ S3 thành Polars DataFrame."""
    logger.info(f"Đọc dữ liệu từ s3://{bucket}/{key}")
    response = s3_client.get_object(Bucket=bucket, Key=key)
    
    # Đọc bytes object vào memory buffer
    parquet_bytes = response['Body'].read()
    df = pl.read_parquet(io.BytesIO(parquet_bytes))
    return df

def write_parquet_to_s3(df: pl.DataFrame, bucket: str, key: str) -> None:
    """Ghi Polars DataFrame thành Parquet lên S3."""
    logger.info(f"Ghi dữ liệu lên s3://{bucket}/{key}")
    
    buffer = io.BytesIO()
    df.write_parquet(buffer)
    buffer.seek(0)
    
    s3_client.put_object(
        Bucket=bucket, 
        Key=key, 
        Body=buffer.getvalue()
    )
    logger.info("Lưu file Parquet lên S3 thành công.")