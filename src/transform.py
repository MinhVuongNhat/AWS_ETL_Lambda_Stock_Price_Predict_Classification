import polars as pl
from logger import get_logger

logger = get_logger(__name__)


class DataTransformError(Exception):
    pass


def apply_feature_engineering(df: pl.DataFrame) -> pl.DataFrame:
    """
    Thực hiện Feature Engineering đầy đủ cho bài toán dự đoán giá cổ phiếu.
    """
    logger.info("-> Đang thực hiện Feature Engineering (đầy đủ indicators)...")

    # Đảm bảo dữ liệu được sắp xếp theo thời gian trước khi tính rolling/EWM
    df = df.sort(["Symbol", "Date"])
    
    # Label: 1 nếu giá đóng cửa T+1 > T, ngược lại 0
    df = df.with_columns([
        pl.col("Close").shift(-1).over("Symbol").alias("_Next_Close"),
    ])
    df = df.with_columns([
        (pl.col("_Next_Close") > pl.col("Close"))
        .cast(pl.Int8)
        .alias("Label")
    ])
    df = df.drop("_Next_Close")

    # Bước 1: Trend + Lag + Return — tính song song trong 1 pass
    df = df.with_columns([
        # ----- Trend -----
        # SMA: Simple Moving Average
        pl.col("Adj Close").rolling_mean(window_size=5).over("Symbol").alias("SMA_5"),
        pl.col("Adj Close").rolling_mean(window_size=20).over("Symbol").alias("SMA_20"),

        # EMA: Exponential Moving Average
        # span=N → alpha = 2/(N+1), adjust=False = EMA kiểu truyền thống (recursive)
        pl.col("Adj Close").ewm_mean(span=12, adjust=False).over("Symbol").alias("EMA_12"),
        pl.col("Adj Close").ewm_mean(span=26, adjust=False).over("Symbol").alias("EMA_26"),

        # ----- Lag Features -----
        pl.col("Close").shift(1).over("Symbol").alias("Lag_Close_1"),
        pl.col("Close").shift(2).over("Symbol").alias("Lag_Close_2"),
        pl.col("Close").shift(3).over("Symbol").alias("Lag_Close_3"),

        # ----- Daily Return -----
        (pl.col("Adj Close") / pl.col("Adj Close").shift(1) - 1).over("Symbol").alias("Daily_Return"),

        # ----- Intraday Volatility (không cần lịch sử) -----
        ((pl.col("High") - pl.col("Low")) / pl.col("Open")).alias("Intraday_Volatility"),
    ])

    # Bước 2: MACD = EMA_12 - EMA_26
    df = df.with_columns([
        (pl.col("EMA_12") - pl.col("EMA_26")).alias("MACD"),
    ])

    # Bước 3: MACD_Signal = EMA_9 của MACD  |  MACD_Hist = MACD - Signal
    df = df.with_columns([
        pl.col("MACD").ewm_mean(span=9, adjust=False).over("Symbol").alias("MACD_Signal"),
    ])
    df = df.with_columns([
        (pl.col("MACD") - pl.col("MACD_Signal")).alias("MACD_Hist"),
    ])

    # Bước 4: RSI_14 — Wilder's Smoothing Method
    df = df.with_columns([
        pl.col("Adj Close").diff().over("Symbol").alias("_price_delta"),
    ])
    df = df.with_columns([
        pl.col("_price_delta").clip(lower_bound=0).alias("_gain"),
        (-pl.col("_price_delta")).clip(lower_bound=0).alias("_loss"),
    ])
    df = df.with_columns([
        pl.col("_gain").ewm_mean(alpha=1.0 / 14.0, adjust=False).over("Symbol").alias("_avg_gain"),
        pl.col("_loss").ewm_mean(alpha=1.0 / 14.0, adjust=False).over("Symbol").alias("_avg_loss"),
    ])
    df = df.with_columns([
        (100.0 - 100.0 / (1.0 + pl.col("_avg_gain") / pl.col("_avg_loss"))).alias("RSI_14"),
    ])
    df = df.drop(["_price_delta", "_gain", "_loss", "_avg_gain", "_avg_loss"])

    # Bước 5: Bollinger Bands
    df = df.with_columns([
        pl.col("Adj Close").rolling_std(window_size=20).over("Symbol").alias("_std_20"),
    ])
    df = df.with_columns([
        (pl.col("SMA_20") + 2.0 * pl.col("_std_20")).alias("BB_Upper"),
        (pl.col("SMA_20") - 2.0 * pl.col("_std_20")).alias("BB_Lower"),
    ])
    df = df.with_columns([
        ((pl.col("BB_Upper") - pl.col("BB_Lower")) / pl.col("SMA_20")).alias("BB_Width"),
    ])
    df = df.drop("_std_20")

    logger.info(
        "-> Feature Engineering hoàn tất. Columns mới: "
        "SMA_5, SMA_20, EMA_12, EMA_26, MACD, MACD_Signal, MACD_Hist, "
        "RSI_14, BB_Upper, BB_Lower, BB_Width, "
        "Lag_Close_1/2/3, Daily_Return, Intraday_Volatility"
    )
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
    [Pipeline A - Historical Backfill]
    Orchestrator điều phối toàn bộ tầng Transform cho backfill.
    """
    try:
        logger.info("=== [TRANSFORM STAGE - BACKFILL] Bắt đầu quá trình biến đổi dữ liệu ===")

        # 1. Feature Engineering (cần toàn bộ lịch sử để rolling window chính xác)
        df_featured = apply_feature_engineering(df)

        # 2. Rename / Normalize
        df_normalized = normalize_columns(df_featured)

        # 3. Partitioning theo năm
        partitioned_data = partition_data_by_year(df_normalized)

        logger.info(f"Hoàn tất Transform. Đã phân thành {len(partitioned_data)} partitions.")
        return partitioned_data

    except Exception as e:
        logger.error(f"Lỗi trong quá trình Transform: {str(e)}")
        raise DataTransformError(f"Transform Failed: {str(e)}")


def apply_incremental_transform(year_df: pl.DataFrame, new_daily_df: pl.DataFrame) -> pl.DataFrame:
    """
    [Pipeline B - Daily Increment]
    Merge dữ liệu ngày mới vào DataFrame năm hiện tại, sau đó recalculate toàn bộ
    Feature Engineering để đảm bảo SMA, EMA, RSI và các rolling indicator không bị Null.
    """
    try:
        logger.info("=== [TRANSFORM STAGE - DAILY INCREMENT] Bắt đầu Merge & Recalculate ===")
        logger.info(f"  Year DF: {year_df.height} dòng | New daily: {new_daily_df.height} dòng")

        # Toàn bộ các cột Feature Engineering được tính bởi apply_feature_engineering.
        feature_cols = [
            # Trend
            "SMA_5", "SMA_20", "EMA_12", "EMA_26",
            # Momentum
            "MACD", "MACD_Signal", "MACD_Hist", "RSI_14",
            # Volatility
            "BB_Upper", "BB_Lower", "BB_Width", "Intraday_Volatility",
            # Lag & Return
            "Lag_Close_1", "Lag_Close_2", "Lag_Close_3", "Daily_Return",
        ]

        # Drop feature columns cũ trong year_df để tránh conflict khi concat
        existing_feature_cols = [c for c in feature_cols if c in year_df.columns]
        if existing_feature_cols:
            year_df_base = year_df.drop(existing_feature_cols)
        else:
            year_df_base = year_df

        # Đổi tên 'Adj_Close' -> 'Adj Close' trong year_df_base để đồng nhất với new_daily_df
        if "Adj_Close" in year_df_base.columns:
            year_df_base = year_df_base.rename({"Adj_Close": "Adj Close"})

        # Bước 2: Concat và loại bỏ duplicate (ưu tiên dữ liệu mới nhất)
        merged_df = pl.concat([year_df_base, new_daily_df], how="diagonal_relaxed")
        rows_before = merged_df.height
        merged_df = merged_df.unique(subset=["Symbol", "Date"], keep="last")
        logger.info(f"  Sau merge: {merged_df.height} dòng ({rows_before - merged_df.height} duplicate đã xóa)")

        # Bước 3: Recalculate toàn bộ Feature Engineering trên year DataFrame đầy đủ.
        df_featured = apply_feature_engineering(merged_df)

        # Bước 4: Normalize lại cột
        df_normalized = normalize_columns(df_featured)

        logger.info(f"✅ Hoàn tất Incremental Transform. Tổng: {df_normalized.height} dòng.")
        return df_normalized

    except Exception as e:
        logger.error(f"Lỗi trong quá trình Incremental Transform: {str(e)}")
        raise DataTransformError(f"Incremental Transform Failed: {str(e)}")