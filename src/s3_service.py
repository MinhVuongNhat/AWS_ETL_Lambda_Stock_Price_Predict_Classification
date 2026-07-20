import io
import os
from pathlib import Path
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


def check_object_exists_in_s3(bucket: str, key: str) -> bool:
    """Kiểm tra xem một object có tồn tại trên S3 không."""
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except s3_client.exceptions.ClientError:
        return False


def delete_s3_objects(bucket: str, keys: list[str]) -> None:
    """
    Xóa hàng loạt các object khỏi S3
    """
    if not keys:
        return

    logger.info(f"Đang xóa {len(keys)} object khỏi s3://{bucket}/...")

    # Chia thành từng batch 1000 key
    batch_size = 1000
    for i in range(0, len(keys), batch_size):
        batch = keys[i:i + batch_size]
        delete_payload = {'Objects': [{'Key': k} for k in batch]}
        response = s3_client.delete_objects(Bucket=bucket, Delete=delete_payload)

        deleted_count = len(response.get('Deleted', []))
        errors = response.get('Errors', [])

        logger.info(f"  -> Đã xóa {deleted_count} object.")
        if errors:
            logger.warning(f"  -> {len(errors)} object xóa thất bại: {errors}")


def upload_directory_to_s3(local_dir: Path, bucket: str, prefix: str) -> int:
    """
    Upload toàn bộ nội dung một thư mục local lên S3.
    Dùng bởi local_backfill.py để đẩy processed/ lên S3 sau backfill.
    """
    local_dir = Path(local_dir)
    if not local_dir.exists():
        raise FileNotFoundError(f"Thư mục không tồn tại: {local_dir}")

    uploaded = 0
    for file_path in local_dir.rglob('*'):
        if not file_path.is_file():
            continue

        # Tính relative path để giữ nguyên cấu trúc thư mục
        relative_path = file_path.relative_to(local_dir)
        s3_key = f"{prefix.rstrip('/')}/{relative_path.as_posix()}"

        logger.info(f"Uploading {file_path.name} -> s3://{bucket}/{s3_key}")
        s3_client.upload_file(str(file_path), bucket, s3_key)
        uploaded += 1

    logger.info(f"✅ Hoàn tất upload {uploaded} file lên s3://{bucket}/{prefix}")
    return uploaded