import os
import sys
import glob
import time
import polars as pl

# Đường dẫn để import các module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from cleaning import clean_data
from validator import validate_data

def run_local_batch():
    raw_dir = "raw"
    processed_dir = "processed"
    
    # Tạo thư mục processed
    os.makedirs(processed_dir, exist_ok=True)
    
    # Lấy danh sách toàn bộ 65 file parquet
    file_list = glob.glob(f"{raw_dir}/*.parquet")
    file_list.sort() # Sắp xếp theo năm từ 1962 -> 2026
    
    print(f"Tìm thấy {len(file_list)} file. Bắt đầu xử lý ...")
    
    success_count = 0
    start_time = time.time()
    
    for file_path in file_list:
        filename = os.path.basename(file_path)
        output_path = os.path.join(processed_dir, filename)
        
        print(f"\n--- Đang xử lý: {filename} ---")
        try:
            # 1. Extract (Đọc từ Local)
            raw_df = pl.read_parquet(file_path)
            
            # debug
            bad = raw_df.filter(pl.col("Open") <= 0)

            if bad.height > 0:
                print("=" * 80)
                print(filename)
                print(bad.select([
                    "Date",
                    "Symbol",
                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Adj Close",
                    "Volume"
                ]).head(20))
                        
            # 2. Transform (Làm sạch & Validate)
            cleaned_df = clean_data(raw_df)
            validated_df = validate_data(cleaned_df)
            
            # 3. Load (Ghi ra Local)
            validated_df.write_parquet(output_path)
            
            success_count += 1
            print(f"✅ Thành công! Đã lưu: {output_path}")
            
        except Exception as e:
            print(f"❌ Lỗi tại file {filename}: {str(e)}")
            # Không raise e để vòng lặp tiếp tục chạy với file năm khác

    total_time = time.time() - start_time
    print(f"\nHOÀN TẤT! Xử lý thành công {success_count}/{len(file_list)} file trong {total_time:.2f} giây.")

if __name__ == "__main__":
    run_local_batch()