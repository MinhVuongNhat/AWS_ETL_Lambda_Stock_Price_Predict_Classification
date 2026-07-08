import polars as pl
import pandera as pa
from schemas import finance_schema
from logger import get_logger

logger = get_logger(__name__)

class DataValidationError(Exception):
    pass

def validate_data(df: pl.DataFrame) -> pl.DataFrame:
    try:
        logger.info("Bắt đầu kiểm tra dữ liệu bằng Pandera...")
        # Validate data với Schema
        validated_df = finance_schema.validate(df)
        logger.info("Dữ liệu hợp lệ, pass toàn bộ Business Rules.")
        return validated_df
        
    except pa.errors.SchemaError as e:
        logger.error(f"Lỗi Schema/Business Rule: {str(e)}")
        raise DataValidationError(f"Invalid data: {str(e)}")
    except Exception as e:
        logger.error(f"Lỗi không xác định khi validate: {str(e)}")
        raise DataValidationError(f"Validation failed: {str(e)}")