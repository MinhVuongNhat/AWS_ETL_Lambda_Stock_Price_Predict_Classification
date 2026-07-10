import polars as pl
from pathlib import Path
from logger import get_logger

logger = get_logger(__name__)

def generate_quality_report(
    df_validated: pl.DataFrame, 
    original_height: int, 
    duplicate_count: int, 
    filename: str
) -> dict:
    """
    Thống kê chi tiết chất lượng dữ liệu dựa trên kết quả gắn cờ từ tầng Validator.
    """
    logger.info(f"=== [REPORT STAGE] Biên soạn báo cáo chất lượng dữ liệu cho file: {filename} ===")
    
    # Tính toán chi tiết các lỗi nghiệp vụ dựa trên cờ 'invalid_reason'
    neg_price = df_validated.filter(pl.col("invalid_reason").str.contains("NEGATIVE_OR_ZERO_PRICE")).height
    neg_volume = df_validated.filter(pl.col("invalid_reason").str.contains("NEGATIVE_VOLUME")).height
    missing_val = df_validated.filter(pl.col("invalid_reason").str.contains("MISSING_VALUE")).height
    total_quarantined = df_validated.filter(pl.col("invalid_reason") != "").height
    clean_rows = df_validated.filter(pl.col("invalid_reason") == "").height

    metrics = {
        "File_Name": filename,
        "Original_Rows": original_height,
        "Duplicate_Dropped": duplicate_count,
        "Negative_Price_Rows": neg_price,
        "Negative_Volume_Rows": neg_volume,
        "Missing_Value_Rows": missing_val,
        "Total_Quarantined": total_quarantined,
        "Clean_Processed_Rows": clean_rows
    }
    return metrics

def save_batch_quality_report(all_metrics: list[dict], report_path: Path) -> None:
    """
    Tổng hợp danh sách các metrics của toàn bộ batch thành một file CSV duy nhất.
    """
    if not all_metrics:
        logger.warning("Không có dữ liệu thống kê để xuất báo cáo.")
        return
        
    report_df = pl.DataFrame(all_metrics)
    
    # Sắp xếp cột báo cáo
    cols_order = ["File_Name", "Original_Rows", "Duplicate_Dropped", "Negative_Price_Rows", 
                  "Negative_Volume_Rows", "Missing_Value_Rows", "Total_Quarantined", "Clean_Processed_Rows"]
    report_df = report_df.select(cols_order)
    
    report_df.write_csv(report_path)
    logger.info(f"📊 Đã ghi nhận báo cáo tổng kết chất lượng dữ liệu tại: {report_path}")