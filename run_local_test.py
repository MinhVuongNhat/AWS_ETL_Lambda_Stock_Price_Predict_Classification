import os
import sys
import time
import polars as pl
from pathlib import Path

# Trỏ đường dẫn để Python nhận diện thư mục src/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from cleaning import clean_data
from validator import validate_data, verify_clean_schema_contract
from quarantine import split_valid_invalid
from report import generate_quality_report, save_batch_quality_report
from transform import transform_pipeline

# Cấu hình đường dẫn padlib
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"

RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
QUARANTINE_DIR = DATA_DIR / "quarantine"
REPORT_DIR = DATA_DIR / "reports"
CLEANSED_DIR = DATA_DIR / "cleansed"

def run_local_batch():
    # 1. Khởi tạo cấu trúc thư mục Output
    for directory in [PROCESSED_DIR, QUARANTINE_DIR, REPORT_DIR, CLEANSED_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    
    file_list = sorted(RAW_DIR.glob("*.parquet"))
    print(f"TÌM THẤY {len(file_list)} FILE TRONG RAW. KHỞI ĐỘNG LOCAL ETL BATCH...")
    
    success_count = 0
    start_time = time.time()
    all_metrics = []
    
    # ==========================================
    # GIAI ĐOẠN 1: MÔ PHỎNG QUALITY GATE (S3 TRIGGER)
    # ==========================================
    for file_path in file_list:
        filename = file_path.name
        symbol_name = file_path.stem
        print(f"\n[{symbol_name}] Đang nạp vào Pipeline...")
        
        try:
            # 1. EXTRACT
            raw_df = pl.read_parquet(file_path)
            original_rows = raw_df.height
            
            # 2. CLEANING
            cleaned_df, duplicate_count = clean_data(raw_df)
            
            # 3. VALIDATION
            validated_df = validate_data(cleaned_df)
            
            # 4. QUARANTINE
            clean_df, quarantine_df = split_valid_invalid(validated_df)
            
            # 5. REPORT METRICS
            metrics = generate_quality_report(validated_df, original_rows, duplicate_count, filename)
            all_metrics.append(metrics)
            print(f"   => Sạch: {metrics['Clean_Processed_Rows']} dòng | Lỗi: {metrics['Total_Quarantined']} dòng.")
            
            # 6. LOAD CLEANSED (CHỈ LƯU VÙNG ĐỆM - KHÔNG TRANSFORM)
            if clean_df.height > 0:
                final_clean_df = verify_clean_schema_contract(clean_df)
                
                # CHỈNH SỬA TẠI ĐÂY: Lưu nguyên file vào thư mục Cleansed (vd: cleansed/AAPL.parquet)
                final_clean_df.write_parquet(CLEANSED_DIR / filename, use_pyarrow=True)
                print("   ✅ Đã lưu dữ liệu sạch vào vùng đệm (Cleansed).")
            else:
                print("   ⚠️ Không có dữ liệu sạch để lưu vào vùng đệm.")
            
            # 7. QUARANTINE LOAD
            if quarantine_df.height > 0:
                quarantine_df.write_parquet(QUARANTINE_DIR / f"error_{filename}", use_pyarrow=True)
                print(f"   ⚠️ Đã cách ly {quarantine_df.height} dòng lỗi.")
                
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ LỖI TẠI {symbol_name}: {str(e)}")

    # 8. KẾT THÚC QUALITY GATE: XUẤT BÁO CÁO TỔNG
    save_batch_quality_report(all_metrics, REPORT_DIR / "master_quality_report.csv")
    
    # ==========================================
    # GIAI ĐOẠN 2: MÔ PHỎNG BATCH ETL JOB ĐÊM
    # ==========================================
    print("\n KHỞI ĐỘNG BATCH ETL JOB ĐÊM...")
    
    # Lúc này glob("*.parquet") sẽ hoạt động hoàn hảo vì file nằm ngay trong Cleansed
    cleansed_files = list(CLEANSED_DIR.glob("*.parquet"))
    
    if cleansed_files:
        print(f"Tìm thấy {len(cleansed_files)} file sạch trong Cleansed Zone. Bắt đầu gộp và Transform...")
        
        # Nạp toàn bộ file từ Cleansed vào danh sách
        df_list = [pl.read_parquet(f) for f in cleansed_files]
        master_df = pl.concat(df_list, how="vertical")
        
        # CHỈNH SỬA TẠI ĐÂY: Chạy Transform & Feature Engineering 1 lần duy nhất cho toàn bộ dữ liệu
        partitioned_data = transform_pipeline(master_df)
        
        # Xuất ra thư mục Processed đúng chuẩn 65 năm
        for year, part_df in partitioned_data.items():
            part_df.write_parquet(PROCESSED_DIR / f"{year}.parquet", use_pyarrow=True)
            
        print("✅ Hoàn tất Transform và lưu các file năm (1962.parquet...)")
    else:
        print("⚠️ Không có file nào trong Cleansed Zone để chạy Batch Job.")
        
    total_time = time.time() - start_time
    print(f"\nKẾT THÚC BATCH! Xử lý thành công {success_count}/{len(file_list)} file trong {total_time:.2f} giây.")

if __name__ == "__main__":
    run_local_batch()