import polars as pl
import pandera.polars as pa
from logger import get_logger
from schemas import finance_strict_schema

logger = get_logger(__name__)

class DataValidationError(Exception):
    pass

def validate_data(df: pl.DataFrame) -> pl.DataFrame:
    """
    CHỈ KIỂM TRA: Quét toàn bộ Business Rules và đánh dấu lỗi vào cột 'invalid_reason'.
    Không xóa hay loại bỏ dòng nào ở bước này.
    """
    try:
        logger.info("=== [VALIDATION STAGE] Bắt đầu rà soát dữ liệu & Business Rules ===")
        
        price_cols = ["Open", "High", "Low", "Close", "Adj Close"]
        essential_cols = ["Date", "Symbol", "Open", "High", "Low", "Close", "Volume"]
        
        # Khởi tạo cột đánh dấu lỗi lý do trống
        df = df.with_columns(pl.lit("").alias("invalid_reason"))

        # Rule 1: Kiểm tra giá âm hoặc bằng 0 (Price <= 0)
        df = df.with_columns(
            pl.when(pl.any_horizontal(pl.col(price_cols) <= 0))
            .then(pl.col("invalid_reason") + "NEGATIVE_OR_ZERO_PRICE;")
            .otherwise(pl.col("invalid_reason"))
        )

        # Rule 2: Kiểm tra Khối lượng giao dịch âm (Volume < 0)
        df = df.with_columns(
            pl.when(pl.col("Volume") < 0)
            .then(pl.col("invalid_reason") + "NEGATIVE_VOLUME;")
            .otherwise(pl.col("invalid_reason"))
        )

        # Rule 3: Kiểm tra Giá trị khuyết thiếu (Null / NaN) ở các trường bắt buộc
        df = df.with_columns(
            pl.when(pl.any_horizontal(pl.col(essential_cols).is_null()))
            .then(pl.col("invalid_reason") + "MISSING_VALUE;")
            .otherwise(pl.col("invalid_reason"))
        )

        logger.info("-> Hoàn tất quét luật nghiệp vụ. Đã gắn cờ 'invalid_reason' thành công.")
        return df

    except Exception as e:
        logger.error(f"Lỗi hệ thống khi thực hiện validation: {str(e)}")
        raise DataValidationError(f"Validation Engine Error: {str(e)}")

def verify_clean_schema_contract(df_clean: pl.DataFrame) -> pl.DataFrame:
    """
    Chốt chặn Pandera Schema Contract: Đảm bảo dữ liệu sạch tuyệt đối tuân thủ kiểu dữ liệu của DWH.
    """
    try:
        if df_clean.height == 0:
            return df_clean
        return finance_strict_schema.validate(df_clean)
    except Exception as e:
        logger.error(f"Dữ liệu Sạch không vượt qua được chốt chặn Pandera Contract: {str(e)}")
        raise DataValidationError(f"Pandera Contract Violation: {str(e)}")