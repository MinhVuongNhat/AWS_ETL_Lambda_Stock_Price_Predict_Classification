import polars as pl
from pathlib import Path

current_dir = Path(__file__).parent.resolve()
project_root = current_dir.parent
data_dir = project_root / "data"
raw_dir = data_dir / "dirty"
quarantine_dir = data_dir / "quarantine"
output_dir = data_dir / "raw"

output_dir.mkdir(parents=True, exist_ok=True)

# Gom dữ liệu sạch
parquet_files = list(raw_dir.rglob("*.parquet"))
print(f"Bắt đầu xử lý {len(parquet_files)} files SẠCH...")

df_list = []
for file_path in parquet_files:
    symbol = file_path.stem
    asset_type = file_path.parent.name
    
    schema = pl.read_parquet_schema(file_path)
    lf = pl.scan_parquet(file_path)
    
    if "Adj Close" not in schema:
        lf = lf.with_columns(pl.col("Close").alias("Adj Close"))
    if "Volume" not in schema:
        lf = lf.with_columns(pl.lit(0).alias("Volume"))
        
    lf = lf.with_columns([
        pl.lit(symbol).alias("Symbol"),
        pl.lit(asset_type).alias("Asset_Type"),
        pl.col("Date").cast(pl.Datetime).dt.date().alias("Date"),
        pl.col("Date").dt.year().alias("Year"),
        pl.col("Open").cast(pl.Float64),
        pl.col("High").cast(pl.Float64),
        pl.col("Low").cast(pl.Float64),
        pl.col("Close").cast(pl.Float64),
        pl.col("Adj Close").cast(pl.Float64),
        pl.col("Volume").cast(pl.Int64)
    ]).select(["Date", "Year", "Symbol", "Asset_Type", "Open", "High", "Low", "Close", "Adj Close", "Volume"])
    
    df_list.append(lf.collect())

if df_list:
    master_df = pl.concat(df_list, how="vertical")
    years = master_df["Year"].unique().to_list()
    years.sort()

    print(f"Xuất file sạch theo năm: {years}")
    for y in years:
        output_file_path = output_dir / f"raw_data_parquet_{y}.parquet"
        (
            master_df
            .filter(pl.col("Year") == y)
            .write_parquet(output_file_path, use_pyarrow=True)
        )

# Gom dữ liệu bị loại bỏ
quarantine_files = list(quarantine_dir.rglob("*.parquet"))
if quarantine_files:
    print(f"\nBắt đầu gộp {len(quarantine_files)} files QUARANTINE...")
    q_list = []
    
    for q_file in quarantine_files:
        asset_type = q_file.parent.name
        q_lf = pl.scan_parquet(q_file).with_columns(
            pl.lit(asset_type).alias("Asset_Type")
        )
        q_list.append(q_lf.collect())
        
    if q_list:
        master_quarantine = pl.concat(q_list, how="diagonal") # diagonal để tự động merge schema nếu có sai lệch nhỏ
        q_output_path = quarantine_dir / "master_quarantine.parquet"
        master_quarantine.write_parquet(q_output_path, use_pyarrow=True)
        print(f" -> Đã lưu file lỗi tổng tại: {q_output_path.name}")

print("\nHoàn tất toàn bộ Pipeline.")