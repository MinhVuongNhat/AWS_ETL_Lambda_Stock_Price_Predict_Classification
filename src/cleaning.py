import polars as pl
from logger import get_logger

logger = get_logger(__name__)

class DataCleaningError(Exception):
    pass

def clean_data(df: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame, dict]:
    """
    Thực hiện Auto-fix và Phân loại dữ liệu (Clean / Quarantine).
    """
    try:
        original_rows = df.height
        
        # LEVEL 1: AUTO-FIX & DEDUPLICATE
        df = df.with_columns([
            pl.col("Date").cast(pl.Date, strict=False),
            pl.col("Year").cast(pl.Int64, strict=False),
            pl.col("Volume").cast(pl.Int64, strict=False)
        ])
        
        df = df.sort(["Symbol", "Date"])
        df = df.unique(subset=["Date", "Symbol"], keep="last")
        total_duplicates = original_rows - df.height
        
        df = df.with_columns([
            pl.max_horizontal("Open", "Close", "High").alias("High"),
            pl.min_horizontal("Open", "Close", "Low").alias("Low")
        ])
        
        # LEVEL 2: QUARANTINE VALIDATION
        price_cols = ["Open", "High", "Low", "Close", "Adj Close"]
        df = df.with_columns(pl.lit("").alias("invalid_reason"))
        
        # Rule A: Lỗi giá
        df = df.with_columns(
            pl.when(pl.any_horizontal(pl.col(price_cols) <= 0))
            .then(pl.col("invalid_reason") + "NEGATIVE_OR_ZERO_PRICE;")
            .otherwise(pl.col("invalid_reason"))
        )
        
        # Rule B: Lỗi Volume
        df = df.with_columns(
            pl.when(pl.col("Volume") < 0)
            .then(pl.col("invalid_reason") + "NEGATIVE_VOLUME;")
            .otherwise(pl.col("invalid_reason"))
        )
        
        # Rule C: Thiếu dữ liệu
        essential_cols = price_cols + ["Volume", "Date", "Symbol"]
        df = df.with_columns(
            pl.when(pl.any_horizontal(pl.col(essential_cols).is_null()))
            .then(pl.col("invalid_reason") + "MISSING_VALUE;")
            .otherwise(pl.col("invalid_reason"))
        )
        
        # LEVEL 3: PHÂN TÁCH & GHI NHẬN METRICS
        clean_df = df.filter(pl.col("invalid_reason") == "")
        quarantine_df = df.filter(pl.col("invalid_reason") != "")
        
        # Dọn dẹp clean_df
        clean_df = clean_df.drop("invalid_reason")
        
        # Tổ chức lại cột cho quarantine_df
        if quarantine_df.height > 0:
            cols = ["Date", "Symbol", "invalid_reason"]
            other_cols = [c for c in quarantine_df.columns if c not in cols]
            quarantine_df = quarantine_df.select(cols + other_cols)
            
        metrics = {
            "Original_Rows": original_rows,
            "Duplicate_Dropped": total_duplicates,
            "Negative_Count": df.filter(pl.col("invalid_reason").str.contains("NEGATIVE")).height,
            "Missing_Count": df.filter(pl.col("invalid_reason").str.contains("MISSING")).height,
            "Quarantined_Rows": quarantine_df.height,
            "Clean_Rows": clean_df.height
        }
        
        return clean_df, quarantine_df, metrics
        
    except Exception as e:
        logger.error(f"Lỗi khi làm sạch và phân tách dữ liệu: {str(e)}")
        raise DataCleaningError(f"Cleaning Error: {str(e)}")