import os
import contextlib
import logging
import pandas as pd
import polars as pl
import yfinance as yf
from pathlib import Path

# ==================== CẤU HÌNH & HẰNG SỐ ====================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

PROJECT_ROOT = Path.cwd().parent
DATA_DIR = PROJECT_ROOT / "data"

# Kiến trúc mới: Chỉ dùng raw/ và metadata/
RAW_DIR = DATA_DIR / "raw"
METADATA_DIR = DATA_DIR / "metadata"

DIRECTORIES = [RAW_DIR, METADATA_DIR]

NASDAQ_URL = "http://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt"

# ==================== CÁC HÀM XỬ LÝ ====================
def setup_directories(dirs: list):
    """Tạo cấu trúc thư mục làm việc."""
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logging.info("Đã thiết lập xong cấu trúc thư mục Data Lake.")

def fetch_and_clean_metadata() -> pd.DataFrame:
    """Tải và làm sạch nhẹ danh sách mã chứng khoán từ NASDAQ."""
    logging.info("Đang tải danh sách symbols từ NASDAQ...")
    try:
        dirty_data = pd.read_csv(NASDAQ_URL, sep='|')
        clean_data = dirty_data[dirty_data['Test Issue'] == 'N'].copy()
        clean_data = clean_data[~clean_data['NASDAQ Symbol'].str.contains(r'[-=\.\^]', regex=True, na=False)]
        return clean_data
    except Exception as e:
        logging.error(f"Lỗi khi lấy metadata từ NASDAQ: {e}")
        return pd.DataFrame()

# ==================== MAIN EXECUTION ====================
if __name__ == "__main__":
    setup_directories(DIRECTORIES)
    meta_df = fetch_and_clean_metadata()
    
    if meta_df.empty:
        logging.error("Không tải được metadata. Hủy quá trình.")
        exit(1)
        
    symbols = meta_df['NASDAQ Symbol'].tolist()
    symbol_type_map = dict(zip(meta_df['NASDAQ Symbol'], meta_df['ETF']))

    valid_symbols = []

    logging.info(f"Bắt đầu tải {len(symbols)} symbols. Ghi trực tiếp 1 file/symbol vào Raw...")
    
    # Chặn log rác từ thư viện yfinance
    with open(os.devnull, 'w') as devnull:
        with contextlib.redirect_stdout(devnull):
            for symbol in symbols:
                try:
                    # 1. Kéo dữ liệu gốc bằng Pandas
                    df_pd = yf.download(symbol, period='max', progress=False)
                    if df_pd.empty: 
                        continue
                    
                    # Fix cấu trúc MultiIndex của yfinance trả về
                    if isinstance(df_pd.columns, pd.MultiIndex):
                        df_pd.columns = df_pd.columns.droplevel(1)
                    
                    df_pd = df_pd.reset_index()
                    if df_pd['Date'].dt.tz is not None:
                        df_pd['Date'] = df_pd['Date'].dt.tz_localize(None)

                    # 2. Đưa sang Polars để cấu trúc lại Schema (KHÔNG clean, KHÔNG filter)
                    df = pl.from_pandas(df_pd)
                    cols = df.columns
                    asset_type = "etfs" if symbol_type_map.get(symbol) == 'Y' else "stocks"

                    # Đảm bảo cấu trúc cột đồng nhất cho mọi file
                    if "Adj Close" not in cols:
                        df = df.with_columns(pl.col("Close").alias("Adj Close"))
                    if "Volume" not in cols:
                        df = df.with_columns(pl.lit(None, dtype=pl.Int64).alias("Volume"))
                        
                    # Ép kiểu dữ liệu (Data Type Contract) để tầng ETL sau không bị vấp
                    df = df.with_columns([
                        pl.lit(symbol).alias("Symbol"),
                        pl.lit(asset_type).alias("Asset_Type"),
                        pl.col("Date").cast(pl.Datetime, strict=False).dt.date().alias("Date"),
                        pl.col("Date").dt.year().alias("Year"), # Vẫn giữ cột Year để sau này Transform dùng chia Partition
                        pl.col("Open").cast(pl.Float64, strict=False),
                        pl.col("High").cast(pl.Float64, strict=False),
                        pl.col("Low").cast(pl.Float64, strict=False),
                        pl.col("Close").cast(pl.Float64, strict=False),
                        pl.col("Adj Close").cast(pl.Float64, strict=False),
                        pl.col("Volume").cast(pl.Int64, strict=False)
                    ]).select([
                        "Date", "Year", "Symbol", "Asset_Type", 
                        "Open", "High", "Low", "Close", "Adj Close", "Volume"
                    ])
                    
                    # 3. LOAD (Ghi trực tiếp file ra disk, giải phóng RAM ngay lập tức)
                    output_file = RAW_DIR / f"{symbol}.parquet"
                    df.write_parquet(output_file, use_pyarrow=True)
                    
                    valid_symbols.append(symbol)

                except Exception as e:
                    logging.warning(f"Lỗi khi tải {symbol}: {e}")
                    continue

    # 4. Ghi lại danh sách các mã đã tải thành công (Metadata)
    if valid_symbols:
        logging.info("Đang cập nhật Metadata các mã thành công...")
        valid_meta = meta_df[meta_df['NASDAQ Symbol'].isin(valid_symbols)]
        valid_meta[valid_meta['ETF'] == 'N'].to_csv(METADATA_DIR / "symbols_stock.csv", index=False)
        valid_meta[valid_meta['ETF'] == 'Y'].to_csv(METADATA_DIR / "symbols_etf.csv", index=False)

    logging.info(f"🎉 Hoàn tất! Đã tải thành công {len(valid_symbols)} file vào thư mục Raw.")