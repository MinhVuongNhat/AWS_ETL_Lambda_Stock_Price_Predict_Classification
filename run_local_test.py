import os
import sys
import time
import polars as pl
from pathlib import Path
from datetime import datetime

# Trỏ đường dẫn để Python nhận diện thư mục src/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.cleaning import clean_data
from src.validator import validate_data, verify_clean_schema_contract
from src.quarantine import split_valid_invalid
from src.report import generate_quality_report, save_batch_quality_report
from src.transform import apply_incremental_transform

# Cấu hình đường dẫn
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"

RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
QUARANTINE_DIR = DATA_DIR / "quarantine"
REPORT_DIR = DATA_DIR / "reports"
CLEANSED_DAILY_DIR = DATA_DIR / "cleansed_daily"  # Vùng đệm mô phỏng Daily


def simulate_quality_gate(raw_file: Path, today_str: str) -> pl.DataFrame | None:
    """
    [Mô phỏng] Quality Gate Lambda:
    Xử lý 1 file raw và lưu kết quả vào cleansed_daily/{today}/ (local).
    """
    print(f"\n{'='*60}")
    print(f"[MÔ PHỎNG] QUALITY GATE LAMBDA")
    print(f"  File: {raw_file.name}")
    print(f"  Ngày: {today_str}")
    print(f"{'='*60}")

    filename = raw_file.name

    try:
        # EXTRACT
        raw_df = pl.read_parquet(raw_file)
        original_rows = raw_df.height
        print(f"  Đã đọc {original_rows:,} dòng từ raw.")

        # CLEANING
        cleaned_df, duplicate_count = clean_data(raw_df)

        # VALIDATION
        validated_df = validate_data(cleaned_df)

        # QUARANTINE SPLIT
        clean_df, quarantine_df = split_valid_invalid(validated_df)

        # REPORT
        metrics = generate_quality_report(validated_df, original_rows, duplicate_count, filename)
        print(f"  => Sạch: {metrics['Clean_Processed_Rows']} dòng | Lỗi: {metrics['Total_Quarantined']} dòng.")
        save_batch_quality_report([metrics], REPORT_DIR / f"daily_report_{today_str}.csv")

        # LƯU VÀO CLEANSED_DAILY
        if clean_df.height > 0:
            final_clean_df = verify_clean_schema_contract(clean_df)
            daily_dir = CLEANSED_DAILY_DIR / today_str
            daily_dir.mkdir(parents=True, exist_ok=True)
            final_clean_df.write_parquet(daily_dir / filename, use_pyarrow=True)
            print(f"  ✅ Dữ liệu sạch lưu tại: {daily_dir / filename}")
            return final_clean_df
        else:
            print(f"  ⚠️  Không có dữ liệu sạch.")
            return None

    except Exception as e:
        print(f"  ❌ LỖI: {str(e)}")
        return None


def simulate_daily_etl(today_str: str, current_year: int) -> None:
    """
    [Mô phỏng] Daily Increment ETL Lambda:
    1. Tải toàn bộ file từ cleansed_daily/{today}/ (local)
    2. Tải year_df từ processed/{current_year}.parquet
    3. Merge + Recalculate FE
    4. Ghi đè processed/{current_year}.parquet
    """
    print(f"\n{'='*60}")
    print(f"[MÔ PHỎNG] DAILY INCREMENT ETL LAMBDA")
    print(f"  Ngày: {today_str} | Năm: {current_year}")
    print(f"{'='*60}")

    # Quét vùng đệm daily
    daily_dir = CLEANSED_DAILY_DIR / today_str
    if not daily_dir.exists():
        print(f"  ⚠️  Không có dữ liệu trong {daily_dir}. No-op.")
        return

    daily_files = list(daily_dir.glob("*.parquet"))
    if not daily_files:
        print(f"  ⚠️  Không tìm thấy file .parquet trong {daily_dir}. No-op.")
        return

    print(f"  Tìm thấy {len(daily_files)} file sạch cho ngày {today_str}.")

    # Gom dữ liệu ngày mới
    daily_df_list = [pl.read_parquet(f) for f in daily_files]
    new_daily_df = pl.concat(daily_df_list, how="diagonal_relaxed")
    print(f"  Dữ liệu ngày mới: {new_daily_df.height:,} dòng.")

    # Tải year_df
    year_file = PROCESSED_DIR / f"{current_year}.parquet"
    if not year_file.exists():
        print(f"\n  ⚠️  CẢNH BÁO: Không tìm thấy {year_file}!")
        print(f"  Vui lòng chạy 'python local_backfill.py' trước để tạo file năm.")
        print(f"  Đang tạo year_df mới từ dữ liệu ngày hôm nay (FE sẽ kém chính xác)...")
        # Fallback: chỉ dùng dữ liệu ngày hiện tại (SMA sẽ bị Null một phần)
        from src.transform import apply_feature_engineering, normalize_columns
        updated_df = normalize_columns(apply_feature_engineering(new_daily_df))
    else:
        year_df = pl.read_parquet(year_file)
        print(f"  Historical Context: {year_df.height:,} dòng từ {year_file.name}")

        # Merge & Recalculate
        updated_df = apply_incremental_transform(year_df, new_daily_df)

    # Ghi đè file năm
    year_file.parent.mkdir(parents=True, exist_ok=True)
    updated_df.write_parquet(year_file, use_pyarrow=True)
    print(f"  ✅ Đã ghi đè: {year_file} ({updated_df.height:,} dòng)")

    # Hiển thị mẫu kết quả
    print(f"\n  📋 Mẫu kết quả (5 dòng cuối của file năm):")
    tail = updated_df.tail(5)
    feature_cols = ["Date", "Symbol", "Adj_Close", "Daily_Return", "SMA_5", "SMA_20"]
    available_cols = [c for c in feature_cols if c in tail.columns]
    print(tail.select(available_cols).to_pandas().to_string(index=False))

    print(f"\n  ✅ Daily ETL mô phỏng thành công.")


def main():
    # Khởi tạo thư mục output
    for directory in [QUARANTINE_DIR, REPORT_DIR, CLEANSED_DAILY_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    today_str = datetime.now().strftime('%Y-%m-%d')
    current_year = datetime.now().year

    start_time = time.time()
    print(f"\n🚀 MÔ PHỎNG DAILY INCREMENT PIPELINE (Pipeline B)")
    print(f"   Ngày mô phỏng: {today_str}")

    # Lấy 1 file raw đại diện cho "dữ liệu ngày hôm nay"
    file_list = sorted(RAW_DIR.glob("*.parquet"))
    if not file_list:
        print(f"\n❌ Không tìm thấy file .parquet trong {RAW_DIR}")
        print("   Vui lòng đặt dữ liệu raw vào data/raw/ trước khi chạy.")
        sys.exit(1)

    # Mặc định: dùng file đầu tiên để mô phỏng (có thể thay đổi logic này)
    test_file = file_list[0]
    print(f"   File đại diện cho hôm nay: {test_file.name}")

    # MÔ PHỎNG QUALITY GATE
    simulate_quality_gate(test_file, today_str)

    # MÔ PHỎNG DAILY ETL
    simulate_daily_etl(today_str, current_year)

    elapsed = time.time() - start_time
    print(f"\n⏱️  Tổng thời gian mô phỏng: {elapsed:.2f} giây")
    print("✅ MÔ PHỎNG HOÀN TẤT.")
    print(f"\n💡 Để xây dựng toàn bộ dữ liệu lịch sử, hãy chạy:")
    print(f"   python local_backfill.py --upload")


if __name__ == "__main__":
    main()