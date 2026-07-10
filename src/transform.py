import polars as pl
from logger import get_logger

logger = get_logger(__name__)

class DataTransformError(Exception):
    pass

def apply_feature_engineering(df: pl.DataFrame) -> pl.DataFrame:
    """
    Thực hiện Feature Engineering cơ bản.
    """
    logger.info("-> Đang thực hiện Feature Engineering...")
    
    # Đảm bảo dữ liệu được sắp xếp theo thời gian trước khi tính toán các chỉ báo chuỗi thời gian
    df = df.sort(["Symbol", "Date"])
    
    df = df.with_columns([
        # Tính Daily Return
        (pl.col("Adj Close") / pl.col("Adj Close").shift(1) - 1).over("Symbol").alias("Daily_Return"),
        
        # Tính Simple Moving Averages (SMA)
        pl.col("Adj Close").rolling_mean(window_size=5).over("Symbol").alias("SMA_5"),
        pl.col("Adj Close").rolling_mean(window_size=20).over("Symbol").alias("SMA_20"),
        
        # Tính Volatility cơ bản (Biên độ dao động trong ngày)
        ((pl.col("High") - pl.col("Low")) / pl.col("Open")).alias("Intraday_Volatility")
    ])
    return df

def normalize_columns(df: pl.DataFrame) -> pl.DataFrame:
    """
    Chuẩn hóa tên cột.
    """
    logger.info("-> Đang chuẩn hóa tên cột (Rename)...")
    # Đổi 'Adj Close' thành 'Adj_Close' để dễ thao tác hơn trong SQL/Pandas sau này
    if "Adj Close" in df.columns:
        df = df.rename({"Adj Close": "Adj_Close"})
    return df

def partition_data_by_year(df: pl.DataFrame) -> dict[int, pl.DataFrame]:
    """
    Chia tách DataFrame lớn thành một dictionary các DataFrame nhỏ, gom nhóm theo Năm.
    Trả về: {2023: df_2023, 2024: df_2024, ...}
    """
    logger.info("-> Đang phân mảnh (Partition) dữ liệu theo Năm...")
    partitions = {}
    
    # Lấy danh sách các năm duy nhất có trong dữ liệu
    years = df.select("Year").drop_nulls().unique().to_series().to_list()
    
    for year in sorted(years):
        partitioned_df = df.filter(pl.col("Year") == year)
        partitions[year] = partitioned_df
        
    return partitions

def transform_pipeline(df: pl.DataFrame) -> dict[int, pl.DataFrame]:
    """
    Orchestrator điều phối toàn bộ tầng Transform.
    Đầu vào: DataFrame Sạch.
    Đầu ra: Dictionary chứa các DataFrame đã được Feature Engineering và Partition.
    """
    try:
        logger.info("=== [TRANSFORM STAGE] Bắt đầu quá trình biến đổi dữ liệu ===")
        
        # 1. Feature Engineering
        df_featured = apply_feature_engineering(df)
        
        # 2. Rename / Normalize
        df_normalized = normalize_columns(df_featured)
        
        # 3. Partitioning
        partitioned_data = partition_data_by_year(df_normalized)
        
        logger.info(f"Hoàn tất Transform. Đã phân thành {len(partitioned_data)} partitions.")
        return partitioned_data
        
    except Exception as e:
        logger.error(f"Lỗi trong quá trình Transform: {str(e)}")
        raise DataTransformError(f"Transform Failed: {str(e)}")