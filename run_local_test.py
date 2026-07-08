import os
import sys
import time
import polars as pl
from pathlib import Path

# Đường dẫn để import các module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from cleaning import clean_data
from validator import validate_schema_contract

# --- CẤU HÌNH ĐƯỜNG DẪN BẰNG PATHLIB ---
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"

RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
QUARANTINE_DIR = DATA_DIR / "quarantine"
REPORT_DIR = DATA_DIR / "reports"

def run_local_batch():
    # 1. Tạo đầy đủ cấu trúc thư mục bằng pathlib
    for directory in [PROCESSED_DIR, QUARANTINE_DIR, REPORT_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Lấy danh sách toàn bộ file parquet (thay thế glob bằng pathlib.glob)
    file_list = sorted(RAW_DIR.glob("*.parquet"))
    
    print(f"🚀 Tìm thấy {len(file_list)} file. Bắt đầu xử lý ...")
    
    success_count = 0
    start_time = time.time()
    
    # Danh sách lưu trữ thống kê của từng năm để làm Report
    all_metrics = []
    
    for file_path in file_list:
        filename = file_path.name
        output_path = PROCESSED_DIR / filename
        quarantine_path = QUARANTINE_DIR / f"error_{filename}"
        
        print(f"\n--- Đang xử lý: {filename} ---")
        try:
            # 1. Extract
            raw_df = pl.read_parquet(file_path)
            
            # 2. Transform (Làm sạch & Bóc tách)
            cleaned_df, quarantine_df, metrics = clean_data(raw_df)
            
            # Bổ sung tên file vào metrics để dễ track trong Report
            metrics['File_Name'] = filename
            all_metrics.append(metrics)
            
            # In nhanh log ra màn hình
            print(f"Đầu vào: {metrics['Original_Rows']} dòng | Lỗi: {metrics['Quarantined_Rows']} | Sạch: {metrics['Clean_Rows']}")
            
            # 3. Quarantine (Lưu dữ liệu lỗi)
            if quarantine_df.height > 0:
                quarantine_df.write_parquet(quarantine_path)
                print(f"⚠️ Đã cách ly {quarantine_df.height} dòng lỗi vào {quarantine_path.name}")
            
            # 4. Validate & Load (Chốt chặn Data Contract cuối cùng)
            if cleaned_df.height > 0:
                # FIX: Gọi đúng tên hàm validate_schema_contract
                validated_df = validate_schema_contract(cleaned_df)
                validated_df.write_parquet(output_path)
                print(f"✅ Thành công! Đã lưu file sạch.")
            else:
                print(f"⚠️ Không có dữ liệu sạch nào để lưu cho file {filename}.")
                
            success_count += 1
            
        except Exception as e:
            print(f"❌ Lỗi tại file {filename}: {str(e)}")

    # 5. KẾT THÚC VÒNG LẶP: XUẤT REPORT
    if all_metrics:
        # Chuyển list các dictionary thành Polars DataFrame
        report_df = pl.DataFrame(all_metrics)
        
        # Sắp xếp lại: Đưa cột File_Name lên đầu cho dễ nhìn
        cols = ["File_Name"] + [c for c in report_df.columns if c != "File_Name"]
        report_df = report_df.select(cols)
        
        report_path = REPORT_DIR / "batch_quality_report.csv"
        report_df.write_csv(report_path)
        print(f"\n📊 Đã xuất báo cáo chất lượng dữ liệu tổng quát: {report_path}")

    total_time = time.time() - start_time
    print(f"\n🎉 HOÀN TẤT! Xử lý thành công {success_count}/{len(file_list)} file trong {total_time:.2f} giây.")

if __name__ == "__main__":
    run_local_batch()