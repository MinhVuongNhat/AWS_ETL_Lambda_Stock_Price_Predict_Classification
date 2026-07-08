import polars as pl
from logger import get_logger

logger = get_logger(__name__)

class DataCleaningError(Exception):
    pass

def clean_data(df: pl.DataFrame) -> pl.DataFrame:
    try:
        logger.info(f"Bắt đầu làm sạch dữ liệu. Kích thước ban đầu: {df.shape}")
        
        # 1. Ép kiểu dữ liệu an toàn
        df = df.with_columns([
            pl.col("Date").cast(pl.Date, strict=False),
            pl.col("Year").cast(pl.Int64, strict=False),
            pl.col("Volume").cast(pl.Int64, strict=False)
        ])
        
        # Loại bỏ các dòng bị lỗi null Date hoặc Symbol sau khi ép kiểu
        df = df.drop_nulls(subset=["Date", "Symbol"])
        
        # 2. Loại bỏ bản ghi trùng lặp (giữ lại bản ghi cuối cùng theo Date và Symbol)
        df = df.unique(subset=["Date", "Symbol"], keep="last")
        
        # 3. Sắp xếp để chuẩn bị Forward/Backward Fill cho Time Series
        df = df.sort(["Symbol", "Date"])
        
        # 4. Xử lý Missing Values theo nhóm Symbol (Mã cổ phiếu)
        # Điền Forward Fill trước (lấy giá ngày hôm trước điền hôm nay), 
        # sau đó Backward Fill (cho những ngày đầu tiên bị thiếu).
        df = df.with_columns(
            pl.all().exclude(["Date", "Symbol", "Asset_Type"])
              .forward_fill().over("Symbol")
        ).with_columns(
            pl.all().exclude(["Date", "Symbol", "Asset_Type"])
              .backward_fill().over("Symbol")
        )
        
        # Loại bỏ triệt để các dòng vẫn còn Null (nếu có mã nào đó thiếu sạch dữ liệu)
        df = df.drop_nulls()

        logger.info(f"Làm sạch thành công. Kích thước sau clean: {df.shape}")
        return df
        
    except Exception as e:
        logger.error(f"Lỗi khi làm sạch dữ liệu: {str(e)}")
        raise DataCleaningError(f"Cleaning Error: {str(e)}")