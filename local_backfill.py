import os
import sys
import time
import argparse
import polars as pl
from pathlib import Path

# Trỏ đường dẫn để Python nhận diện thư mục src/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.cleaning import clean_data
from src.validator import validate_data, verify_clean_schema_contract
from src.quarantine import split_valid_invalid
from src.report import generate_quality_report, save_batch_quality_report
from src.transform import transform_pipeline

# Cấu hình đường dẫn
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"

RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
QUARANTINE_DIR = DATA_DIR / "quarantine"
REPORT_DIR = DATA_DIR / "reports"
CLEANSED_DIR = DATA_DIR / "cleansed"  # Vùng đệm tạm thời local


def run_quality_gate_stage(file_list: list[Path]) -> pl.DataFrame:
    """
    Giai đoạn 1: Chạy toàn bộ Quality Gate pipeline cho từng file raw.
    Trả về DataFrame tổng hợp toàn bộ dữ liệu sạch.
    """
    print(f"\n{'='*60}")
    print(f"GIAI ĐOẠN 1: QUALITY GATE ({len(file_list)} files)")
    print(f"{'='*60}")

    all_clean_dfs = []
    all_metrics = []
    quarantine_count = 0
    error_count = 0

    for i, file_path in enumerate(file_list, 1):
        filename = file_path.name
        symbol_name = file_path.stem
        print(f"\n[{i}/{len(file_list)}] [{symbol_name}] Đang xử lý...")

        try:
            # EXTRACT
            raw_df = pl.read_parquet(file_path)
            original_rows = raw_df.height

            # CLEANING
            cleaned_df, duplicate_count = clean_data(raw_df)

            # VALIDATION
            validated_df = validate_data(cleaned_df)

            # QUARANTINE SPLIT
            clean_df, quarantine_df = split_valid_invalid(validated_df)

            # REPORT METRICS
            metrics = generate_quality_report(validated_df, original_rows, duplicate_count, filename)
            all_metrics.append(metrics)
            print(f"   => Sạch: {metrics['Clean_Processed_Rows']} dòng | Lỗi: {metrics['Total_Quarantined']} dòng.")

            # LƯU DỮ LIỆU SẠCH vào cleansed/ (vùng đệm local)
            if clean_df.height > 0:
                final_clean_df = verify_clean_schema_contract(clean_df)
                final_clean_df.write_parquet(CLEANSED_DIR / filename, use_pyarrow=True)
                all_clean_dfs.append(final_clean_df)
                print(f"   ✅ Đã lưu dữ liệu sạch vào vùng đệm.")
            else:
                print(f"   ⚠️  Không có dữ liệu sạch để lưu.")

            # LƯU DỮ LIỆU LỖI vào quarantine/
            if quarantine_df.height > 0:
                quarantine_df.write_parquet(QUARANTINE_DIR / f"error_{filename}", use_pyarrow=True)
                quarantine_count += quarantine_df.height

        except Exception as e:
            print(f"   ❌ LỖI TẠI [{symbol_name}]: {str(e)}")
            error_count += 1

    # XUẤT BÁO CÁO TỔNG
    if all_metrics:
        save_batch_quality_report(all_metrics, REPORT_DIR / "master_quality_report.csv")
        print(f"\n📊 Báo cáo chất lượng: {REPORT_DIR / 'master_quality_report.csv'}")

    print(f"\n{'='*60}")
    print(f"KẾT THÚC QUALITY GATE:")
    print(f"  - File xử lý thành công: {len(file_list) - error_count}/{len(file_list)}")
    print(f"  - Dòng cách ly (Quarantine): {quarantine_count}")
    print(f"  - File gặp lỗi: {error_count}")
    print(f"{'='*60}")

    if all_clean_dfs:
        master_df = pl.concat(all_clean_dfs, how="diagonal_relaxed")
        print(f"\n✅ Tổng dữ liệu sạch để Transform: {master_df.height:,} dòng")
        return master_df
    else:
        raise RuntimeError("Không có dữ liệu sạch nào để tiếp tục Transform!")


def run_transform_stage(master_df: pl.DataFrame) -> dict[int, pl.DataFrame]:
    """
    Giai đoạn 2: Transform toàn bộ dữ liệu sạch - Feature Engineering & Partition theo năm.
    """
    print(f"\n{'='*60}")
    print("GIAI ĐOẠN 2: TRANSFORM & FEATURE ENGINEERING")
    print(f"{'='*60}")

    print(f"Đang chạy Feature Engineering & Partition trên {master_df.height:,} dòng...")
    partitioned_data = transform_pipeline(master_df)

    print(f"\nKết quả Partition:")
    for year in sorted(partitioned_data.keys()):
        part_df = partitioned_data[year]
        print(f"  - {year}.parquet: {part_df.height:,} dòng")

    return partitioned_data


def save_processed_files(partitioned_data: dict[int, pl.DataFrame]) -> None:
    """Lưu các file partition năm vào data/processed/."""
    print(f"\n{'='*60}")
    print("GIAI ĐOẠN 3: SAVE TO LOCAL processed/")
    print(f"{'='*60}")

    for year, part_df in sorted(partitioned_data.items()):
        output_path = PROCESSED_DIR / f"{year}.parquet"
        part_df.write_parquet(output_path, use_pyarrow=True)
        print(f"  ✅ Đã lưu: {output_path}")

    print(f"\n✅ Tất cả {len(partitioned_data)} file năm đã được lưu tại: {PROCESSED_DIR}")


def upload_to_s3(processed_dir: Path) -> None:
    """
    Giai đoạn 4 (tùy chọn): Upload toàn bộ processed/ lên S3.
    Sử dụng config từ src/config.py.
    """
    print(f"\n{'='*60}")
    print("GIAI ĐOẠN 4: UPLOAD LÊN S3")
    print(f"{'='*60}")

    # Import ở đây để tránh lỗi nếu boto3 chưa configured khi chạy local-only
    from src.config import PROCESSED_BUCKET, PROCESSED_PREFIX
    from src.s3_service import upload_directory_to_s3

    print(f"Bucket đích: s3://{PROCESSED_BUCKET}/{PROCESSED_PREFIX}")
    print(f"Thư mục nguồn: {processed_dir}")
    print(f"\n Thao tác này sẽ GHI ĐÈ các file năm hiện có trên S3!")

    confirm = input("Bạn có chắc chắn muốn upload không? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Upload đã bị hủy bởi người dùng.")
        return

    uploaded = upload_directory_to_s3(processed_dir, PROCESSED_BUCKET, PROCESSED_PREFIX)
    print(f"\n🎉 Upload hoàn tất! Đã upload {uploaded} file lên S3.")


def main():
    parser = argparse.ArgumentParser(
        description="[Pipeline A] Historical Backfill: ETL toàn bộ dữ liệu raw và upload lên S3."
    )
    parser.add_argument(
        '--upload',
        action='store_true',
        help='Upload processed/ lên S3 sau khi ETL hoàn tất.'
    )
    parser.add_argument(
        '--upload-only',
        action='store_true',
        help='Chỉ upload processed/ đã có sẵn lên S3, bỏ qua bước ETL.'
    )
    args = parser.parse_args()

    # Khởi tạo cấu trúc thư mục output
    for directory in [PROCESSED_DIR, QUARANTINE_DIR, REPORT_DIR, CLEANSED_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    start_time = time.time()

    if args.upload_only:
        # Chỉ upload, bỏ qua ETL
        print("\n📤 Chế độ: Upload Only")
        upload_to_s3(PROCESSED_DIR)
    else:
        # ETL full pipeline
        file_list = sorted(RAW_DIR.glob("*.parquet"))
        if not file_list:
            print(f"❌ Không tìm thấy file .parquet nào trong: {RAW_DIR}")
            print("   Vui lòng đặt dữ liệu raw vào thư mục data/raw/ trước khi chạy.")
            sys.exit(1)

        print(f"\n🚀 KHỞI ĐỘNG HISTORICAL BACKFILL PIPELINE")
        print(f"   Tìm thấy {len(file_list)} file trong {RAW_DIR}")

        # Giai đoạn 1: Quality Gate
        master_df = run_quality_gate_stage(file_list)

        # Giai đoạn 2: Transform & Feature Engineering
        partitioned_data = run_transform_stage(master_df)

        # Giai đoạn 3: Lưu local
        save_processed_files(partitioned_data)

        # Giai đoạn 4 (tùy chọn): Upload S3
        if args.upload:
            upload_to_s3(PROCESSED_DIR)

    elapsed = time.time() - start_time
    print(f"\n Tổng thời gian thực thi: {elapsed:.2f} giây ({elapsed/60:.1f} phút)")
    print("✅ BACKFILL PIPELINE HOÀN TẤT.")


if __name__ == "__main__":
    main()
