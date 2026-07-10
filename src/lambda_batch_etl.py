import polars as pl
from config import CLEANSED_BUCKET, CLEANSED_PREFIX, PROCESSED_BUCKET, PROCESSED_PREFIX
from logger import get_logger

from s3_service import list_parquet_files_in_s3, read_parquet_from_s3, write_parquet_to_s3
from transform import transform_pipeline

logger = get_logger(__name__)

def lambda_handler(event, context):
    """Triggered bởi Cronjob lúc 00:00 mỗi ngày."""
    try:
        logger.info("🚀 KHỞI ĐỘNG NIGHTLY BATCH ETL JOB...")
        
        # 1. Quét toàn bộ file trong thư mục đệm (Cleansed)
        cleansed_keys = list_parquet_files_in_s3(CLEANSED_BUCKET, CLEANSED_PREFIX)
        if not cleansed_keys:
            logger.info("Không có dữ liệu mới trong cleansed/. Kết thúc Job.")
            return {'statusCode': 200, 'body': 'No data to process'}
            
        logger.info(f"Tìm thấy {len(cleansed_keys)} files sạch. Đang nạp vào RAM...")
        
        # 2. Đọc và gom tất cả thành 1 DataFrame lớn (Master DF)
        df_list = []
        for key in cleansed_keys:
            df = read_parquet_from_s3(CLEANSED_BUCKET, key)
            df_list.append(df)
            
        master_df = pl.concat(df_list, how="vertical")
        logger.info(f"Gom nhóm thành công. Tổng khối lượng dữ liệu: {master_df.height} dòng.")
        
        # 3. TRANSFORM (Feature Engineering & Normalize & Partition)
        partitioned_data = transform_pipeline(master_df)
        
        # 4. LOAD (Ghi đè 65 file ra thư mục Processed)
        for year, part_df in partitioned_data.items():
            # Theo kiến trúc của bạn, ghi thẳng file f"{year}.parquet" (vd: 1962.parquet)
            output_key = f"{PROCESSED_PREFIX}{year}.parquet" 
            write_parquet_to_s3(part_df, PROCESSED_BUCKET, output_key)
            
        logger.info("✅ HOÀN TẤT BATCH JOB. Đã lưu dữ liệu vào Processed Zone.")
        
        # 5. (Tùy chọn) Xóa hoặc chuyển file từ Cleansed sang Archive để dọn dẹp không gian
        # Bạn có thể thêm hàm delete object trên S3 ở đây nếu muốn S3 sạch sẽ cho ngày hôm sau.

        return {'statusCode': 200, 'body': 'Batch ETL Completed Successfully'}

    except Exception as e:
        logger.error(f"❌ Lỗi nghiêm trọng tại Batch Job: {str(e)}")
        raise e