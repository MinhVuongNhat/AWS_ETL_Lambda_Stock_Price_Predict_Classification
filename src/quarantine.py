import polars as pl
from pathlib import Path
from logger import get_logger

logger = get_logger(__name__)

def split_valid_invalid(df: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """
    Nhận df đã được validate, bóc tách thành 2 luồng độc lập là Processed và Quarantine.
    """
    logger.info("=== [QUARANTINE STAGE] Bóc tách luồng dữ liệu Sạch và Cách ly ===")
    
    # Lọc luồng dữ liệu sạch (không có lý do lỗi) và dọn bỏ cột thừa
    clean_df = df.filter(pl.col("invalid_reason") == "").drop("invalid_reason")
    
    # Lọc luồng dữ liệu cách ly (có lý do lỗi)
    quarantine_df = df.filter(pl.col("invalid_reason") != "")
    
    # Sắp xếp lại cấu trúc cột cho Quarantine để phục vụ phân tích/điều tra lỗi
    if quarantine_df.height > 0:
        logger.warning(f"⚠️ Phát hiện {quarantine_df.height} dòng lỗi cần đưa vào vùng cách ly.")
        lead_cols = ["Date", "Symbol", "invalid_reason"]
        other_cols = [c for c in quarantine_df.columns if c not in lead_cols]
        quarantine_df = quarantine_df.select(lead_cols + other_cols)
        
    return clean_df, quarantine_df

def write_quarantine_file(df_quarantine: pl.DataFrame, output_path: Path) -> None:
    """Ghi dữ liệu lỗi ra file tập trung dạng Parquet cục bộ hoặc S3 buffer."""
    if df_quarantine.height > 0:
        df_quarantine.write_parquet(output_path, use_pyarrow=True)
        logger.info(f"-> Đã lưu trữ file cách ly thành công tại: {output_path.name}")