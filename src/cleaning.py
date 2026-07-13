import polars as pl
from logger import get_logger

logger = get_logger(__name__)

class DataCleaningError(Exception):
    pass

def clean_data(df: pl.DataFrame) -> tuple[pl.DataFrame, int]:
    """
    Sửa các lỗi chắc chắn sửa được, chuẩn hóa kiểu dữ liệu, xóa trùng lặp.
    không loại bỏ dòng lỗi nghiệp vụ.
    Trả về: (df_cleaned, duplicate_count)
    """
    try:
        original_rows = df.height
        logger.info(f"=== [CLEANING STAGE] Bắt đầu xử lý {original_rows} dòng dữ liệu thô ===")

        # 1. Cast datatype
        df = df.with_columns([
            pl.col("Date").cast(pl.Datetime, strict=False).dt.date().alias("Date"),
            pl.col("Year").cast(pl.Int64, strict=False),
            pl.col("Symbol").cast(pl.String, strict=False),
            pl.col("Asset_Type").cast(pl.String, strict=False),
            pl.col("Open").cast(pl.Float64, strict=False),
            pl.col("High").cast(pl.Float64, strict=False),
            pl.col("Low").cast(pl.Float64, strict=False),
            pl.col("Close").cast(pl.Float64, strict=False),
            pl.col("Adj Close").cast(pl.Float64, strict=False),
            pl.col("Volume").cast(pl.Int64, strict=False)
        ])

        # 2. Sort theo Symbol và Date để đảm bảo tính nhất quán thời gian
        df = df.sort(["Symbol", "Date"])

        # 3. Remove duplicate (Giữ bản ghi cuối cùng - bản ghi cập nhật mới nhất)
        df = df.unique(subset=["Symbol", "Date"], keep="last")
        duplicate_count = original_rows - df.height
        if duplicate_count > 0:
            logger.info(f"-> Đã loại bỏ {duplicate_count} dòng trùng lặp (Deduplicated).")

        # 4. Fix High / Low (Sửa lỗi bo tròn kỹ thuật từ nguồn cấp dữ liệu)
        df = df.with_columns([
            pl.max_horizontal("Open", "Close", "High").alias("High"),
            pl.min_horizontal("Open", "Close", "Low").alias("Low")
        ])

        logger.info(f"-> Hoàn tất Cleaning. Kích thước hiện tại: {df.height} dòng.")
        return df, duplicate_count

    except Exception as e:
        logger.error(f"Gặp lỗi nghiêm trọng trong quá trình clean_data: {str(e)}")
        raise DataCleaningError(f"Cleaning Failed: {str(e)}")