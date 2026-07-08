import polars as pl
from schemas import finance_strict_schema
from logger import get_logger

logger = get_logger(__name__)

class DataValidationError(Exception):
    pass

def validate_schema_contract(df: pl.DataFrame) -> pl.DataFrame:
    try:
        # Pandera giờ chỉ là chốt chặn cuối, đảm bảo Data Warehouse không nhận rác.
        return finance_strict_schema.validate(df)
    except Exception as e:
        logger.error(f"Dữ liệu Clean bị lệch Schema trước khi Load: {str(e)}")
        raise DataValidationError(f"Schema Contract Failed: {str(e)}")