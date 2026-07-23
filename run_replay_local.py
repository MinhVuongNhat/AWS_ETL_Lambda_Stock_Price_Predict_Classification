import argparse
import io
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import polars as pl

# Trỏ đường dẫn để Python nhận diện thư mục src/
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.cleaning import clean_data
from src.validator import validate_data, verify_clean_schema_contract
from src.quarantine import split_valid_invalid
from src.report import generate_quality_report, save_batch_quality_report
from src.transform import apply_incremental_transform, normalize_columns
from src.replay_state import ReplayStateManager
from src.logger import get_logger

logger = get_logger("replay_local")

# Cấu hình đường dẫn local
DATA_DIR          = PROJECT_ROOT / "data"
PROCESSED_DIR     = DATA_DIR / "processed"         # Nguồn: YEAR.parquet gốc
SIM_RAW_DIR       = DATA_DIR / "sim_raw"           # Output: raw/{date}/TICKER.parquet
SIM_PROCESSED_DIR = DATA_DIR / "sim_processed"     # Output: ETL merged files
SIM_CLEANSED_DIR  = DATA_DIR / "sim_cleansed"      # Buffer: sau Quality Gate
SIM_QUARANTINE_DIR = DATA_DIR / "sim_quarantine"   # Dữ liệu lỗi
SIM_REPORTS_DIR   = DATA_DIR / "sim_reports"       # Báo cáo chất lượng
STATE_FILE        = DATA_DIR / "replay_state.json" # Replay state local


BASE_OHLCV_COLS = [
    "Date", "Open", "High", "Low", "Close", "Adj_Close",
    "Volume", "Symbol", "Year", "Asset_Type",
]

# Cache file năm đã load để tránh re-read liên tục
_year_df_cache: dict[int, pl.DataFrame] = {}


def setup_dirs():
    """Tạo tất cả thư mục output nếu chưa có."""
    for d in [SIM_RAW_DIR, SIM_PROCESSED_DIR, SIM_CLEANSED_DIR,
              SIM_QUARANTINE_DIR, SIM_REPORTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

# Step 1: Extract from processed parquet
def load_year_df(year: int) -> pl.DataFrame:
    """Đọc data/processed/YEAR.parquet (có cache)."""
    if year in _year_df_cache:
        return _year_df_cache[year]

    parquet_path = PROCESSED_DIR / f"{year}.parquet"
    if not parquet_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy: {parquet_path}\n"
            f"Vui lòng chạy local_backfill.py trước để tạo file processed/."
        )

    logger.info(f"Đọc {parquet_path}...")
    df = pl.read_parquet(parquet_path)

    # Chỉ giữ cột OHLCV gốc
    available = [c for c in BASE_OHLCV_COLS if c in df.columns]
    df = df.select(available)

    if "Date" in df.columns and df["Date"].dtype != pl.Date:
        df = df.with_columns(pl.col("Date").cast(pl.Date))

    logger.info(f"Năm {year}: {df.height:,} dòng | {df['Symbol'].n_unique()} tickers")
    _year_df_cache[year] = df
    return df


def extract_day_to_sim_raw(trade_date: str) -> int:
    """
    Đọc data năm, filter theo trade_date, lưu từng ticker vào sim_raw/.
    Trả về số ticker đã lưu.
    """
    year = datetime.strptime(trade_date, "%Y-%m-%d").year
    year_df = load_year_df(year)

    trade_date_obj = datetime.strptime(trade_date, "%Y-%m-%d").date()
    df_day = year_df.filter(pl.col("Date") == trade_date_obj)

    if df_day.height == 0:
        logger.warning(f"Không có data cho {trade_date} trong processed/{year}.parquet")
        return 0

    # Đổi Adj_Close → "Adj Close" cho tương thích với Quality Gate
    df_out = df_day
    if "Adj_Close" in df_out.columns:
        df_out = df_out.rename({"Adj_Close": "Adj Close"})

    # Lưu từng ticker
    day_dir = SIM_RAW_DIR / trade_date
    day_dir.mkdir(parents=True, exist_ok=True)

    symbols = df_out["Symbol"].unique().to_list()
    count = 0
    for symbol in symbols:
        ticker_df = df_out.filter(pl.col("Symbol") == symbol)
        out_path = day_dir / f"{symbol}.parquet"
        ticker_df.write_parquet(out_path, use_pyarrow=True)
        count += 1

    logger.info(f"📥 Extract {count} tickers → {day_dir}")
    return count

# Step 2: Quality Gate (local)
def run_quality_gate(trade_date: str) -> pl.DataFrame:
    """
    Chạy Quality Gate pipeline trên sim_raw/{trade_date}/.
    Lưu data sạch vào sim_cleansed/{trade_date}/.
    Trả về DataFrame tổng hợp dữ liệu sạch.
    """
    day_dir = SIM_RAW_DIR / trade_date
    file_list = sorted(day_dir.glob("*.parquet"))

    if not file_list:
        logger.warning(f"Không có file nào trong {day_dir}")
        return pl.DataFrame()

    cleansed_day_dir = SIM_CLEANSED_DIR / trade_date
    cleansed_day_dir.mkdir(parents=True, exist_ok=True)

    all_clean_dfs = []
    all_metrics = []

    for file_path in file_list:
        filename = file_path.name
        symbol = file_path.stem
        try:
            raw_df = pl.read_parquet(file_path)
            original_rows = raw_df.height

            cleaned_df, dup_count = clean_data(raw_df)
            validated_df = validate_data(cleaned_df)
            clean_df, quarantine_df = split_valid_invalid(validated_df)

            metrics = generate_quality_report(validated_df, original_rows, dup_count, filename)
            all_metrics.append(metrics)

            if clean_df.height > 0:
                final_df = verify_clean_schema_contract(clean_df)
                final_df.write_parquet(cleansed_day_dir / filename, use_pyarrow=True)
                all_clean_dfs.append(final_df)

            if quarantine_df.height > 0:
                quarantine_df.write_parquet(
                    SIM_QUARANTINE_DIR / f"error_{trade_date}_{filename}",
                    use_pyarrow=True,
                )

        except Exception as e:
            logger.error(f"  [{symbol}] Quality Gate lỗi: {e}")

    if all_metrics:
        save_batch_quality_report(
            all_metrics,
            SIM_REPORTS_DIR / f"quality_{trade_date}.csv",
        )

    if not all_clean_dfs:
        return pl.DataFrame()

    master = pl.concat(all_clean_dfs, how="diagonal_relaxed")
    logger.info(f"🧹 Quality Gate {trade_date}: {master.height} dòng sạch từ {len(file_list)} tickers")
    return master

# Step 3: ETL (local)
def run_etl(trade_date: str, clean_df: pl.DataFrame) -> None:
    """
    Merge dữ liệu ngày clean_df vào sim_processed/YEAR.parquet.
    Nếu file năm chưa tồn tại, tạo mới từ clean_df.
    """
    if clean_df.height == 0:
        logger.warning(f"ETL {trade_date}: không có data sạch, bỏ qua.")
        return

    year = datetime.strptime(trade_date, "%Y-%m-%d").year
    year_path = SIM_PROCESSED_DIR / f"{year}.parquet"

    if year_path.exists():
        year_df = pl.read_parquet(year_path)
        logger.info(f"ETL: merge {clean_df.height} dòng mới vào {year_path} ({year_df.height} dòng cũ)")
        updated_df = apply_incremental_transform(year_df, clean_df)
    else:
        logger.info(f"ETL: khởi tạo {year_path} từ {clean_df.height} dòng mới")
        # Tạo mới: chỉ cần apply feature engineering
        from src.transform import apply_feature_engineering
        updated_df = apply_feature_engineering(clean_df)
        updated_df = normalize_columns(updated_df)

    updated_df.write_parquet(year_path, use_pyarrow=True)
    logger.info(f"✅ ETL {trade_date}: {updated_df.height} dòng → {year_path}")

# Main Replay Loop
def replay_one_day(trade_date: str, dry_run: bool = False) -> dict:
    """
    Replay đầy đủ pipeline cho 1 ngày giao dịch.
    Trả về dict tóm tắt kết quả.
    """
    logger.info(f"\n{'═'*60}")
    logger.info(f"▶️  REPLAY NGÀY: {trade_date}{' (DRY RUN)' if dry_run else ''}")
    logger.info(f"{'═'*60}")

    t0 = time.time()

    # Step 1: Extract
    ticker_count = extract_day_to_sim_raw(trade_date)
    if ticker_count == 0:
        return {"trade_date": trade_date, "status": "no_data", "elapsed_s": time.time() - t0}

    if dry_run:
        logger.info(f"[DRY RUN] Dừng sau extract. {ticker_count} tickers → sim_raw/")
        return {"trade_date": trade_date, "status": "dry_run_ok", "tickers": ticker_count}

    # Step 2: Quality Gate
    clean_df = run_quality_gate(trade_date)

    # Step 3: ETL
    run_etl(trade_date, clean_df)

    elapsed = time.time() - t0
    result = {
        "trade_date": trade_date,
        "status": "success",
        "tickers_extracted": ticker_count,
        "rows_clean": clean_df.height if clean_df.height > 0 else 0,
        "elapsed_s": round(elapsed, 2),
    }
    logger.info(
        f"✅ Hoàn tất {trade_date} trong {elapsed:.1f}s | "
        f"{ticker_count} tickers | {result['rows_clean']} dòng sạch"
    )
    return result


def run_replay_loop(
    start_date: str,
    end_date: str,
    interval_seconds: int,
    dry_run: bool = False,
    verbose: bool = True,
):
    """
    Vòng lặp replay chính: cứ mỗi interval_seconds thì replay 1 ngày giao dịch.
    """
    setup_dirs()

    state_mgr = ReplayStateManager(local_path=str(STATE_FILE))
    state = state_mgr.initialize(
        start_date=start_date,
        end_date=end_date,
        interval_minutes=interval_seconds // 60,
    )

    print(f"\n{'━'*60}")
    print(f"🚀 REPLAY LOOP BẮT ĐẦU")
    print(f"   Từ: {start_date} → Đến: {end_date}")
    print(f"   Interval: {interval_seconds}s/ngày | Dry run: {dry_run}")
    print(f"   State file: {STATE_FILE}")
    print(f"{'━'*60}\n")

    iteration = 0
    while True:
        state = state_mgr.get_state()

        if state["status"] == "paused":
            print(f"⏸ Replay đang tạm dừng. Chờ {interval_seconds}s...")
            time.sleep(interval_seconds)
            continue

        if state["status"] == "completed":
            print(f"\n🏁 Replay hoàn tất! Đã replay hết data từ {start_date} → {end_date}")
            break

        trade_date = state["current_date"]
        iteration += 1

        print(f"\n[{iteration}] {datetime.now().strftime('%H:%M:%S')} → Replay: {trade_date}")

        try:
            result = replay_one_day(trade_date, dry_run=dry_run)
            if verbose:
                print(f"   📊 {result}")
        except KeyboardInterrupt:
            raise
        except Exception as e:
            logger.error(f"❌ Lỗi replay {trade_date}: {e}")
            print(f"   ❌ LỖI: {e}")

        # Advance state
        new_state = state_mgr.advance()
        next_date = new_state.get("current_date", "N/A")
        total_replayed = new_state.get("total_days_replayed", 0)

        print(f"   ⏩ Ngày tiếp theo: {next_date} | Đã replay: {total_replayed} ngày")

        if new_state["status"] == "completed":
            print(f"\n🏁 Replay hoàn tất! Đã replay hết data.")
            break

        print(f"   💤 Chờ {interval_seconds}s...")
        time.sleep(interval_seconds)

# CLI
def main():
    parser = argparse.ArgumentParser(
        description="Local Replay Runner — Giả lập dòng dữ liệu từ data lịch sử",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  # Replay từ đầu 2025 đến cuối Q1, mỗi 5 giây
  python run_replay_local.py --start 2025-01-02 --end 2025-03-31 --interval 5

  # Dry run: chỉ extract, không chạy QG/ETL
  python run_replay_local.py --start 2025-01-02 --end 2025-01-10 --dry-run

  # Tạm dừng / tiếp tục
  python run_replay_local.py --pause
  python run_replay_local.py --resume

  # Xem trạng thái
  python run_replay_local.py --status
        """,
    )

    parser.add_argument("--start", type=str, default="2025-01-02", help="Ngày bắt đầu replay (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, default="2026-07-18", help="Ngày kết thúc replay (YYYY-MM-DD)")
    parser.add_argument("--interval", type=int, default=60, help="Interval giữa các ngày (giây, default=60 = 1 phút)")
    parser.add_argument("--dry-run", action="store_true", help="Chỉ extract, không chạy QG/ETL")
    parser.add_argument("--pause", action="store_true", help="Tạm dừng replay")
    parser.add_argument("--resume", action="store_true", help="Tiếp tục replay")
    parser.add_argument("--status", action="store_true", help="Xem trạng thái hiện tại")
    parser.add_argument("--quiet", action="store_true", help="Ít log hơn")

    args = parser.parse_args()

    state_mgr = ReplayStateManager(local_path=str(STATE_FILE))

    # Lệnh điều khiển
    if args.status:
        summary = state_mgr.get_summary()
        print("\n📊 REPLAY STATUS")
        print(f"{'─'*40}")
        print(f"  Status          : {summary['status'].upper()}")
        print(f"  Current Date    : {summary['current_date']}")
        print(f"  Replay Range    : {summary['replay_start_date']} → {summary['replay_end_date']}")
        print(f"  Days Replayed   : {summary['total_days_replayed']}")
        print(f"  Days Remaining  : {summary['trading_days_remaining']}")
        print(f"  Last Run (UTC)  : {summary['last_run_utc'] or 'Never'}")
        print(f"  Interval        : {summary['interval_minutes']} min")
        print(f"{'─'*40}")
        return

    if args.pause:
        state = state_mgr.pause()
        print(f"⏸ Replay đã tạm dừng tại ngày: {state['current_date']}")
        return

    if args.resume:
        state = state_mgr.resume()
        print(f"▶️ Replay tiếp tục từ ngày: {state['current_date']}")
        return

    # Chạy replay loop
    try:
        run_replay_loop(
            start_date=args.start,
            end_date=args.end,
            interval_seconds=args.interval,
            dry_run=args.dry_run,
            verbose=not args.quiet,
        )
    except KeyboardInterrupt:
        print("\n\n⛔ Đã dừng bởi người dùng (Ctrl+C).")
        summary = state_mgr.get_summary()
        print(f"   Dừng tại ngày: {summary['current_date']}")
        print(f"   Đã replay: {summary['total_days_replayed']} ngày")
        print(f"\n💡 Chạy lại lệnh để tiếp tục từ ngày {summary['current_date']}.")


if __name__ == "__main__":
    main()
