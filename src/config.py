import os

# S3 Configuration
RAW_BUCKET = os.environ.get('RAW_BUCKET', 'my-nasdaq-stock-market-raw-2026-430970051812-ap-southeast-1-an')
PROCESSED_BUCKET = os.environ.get('PROCESSED_BUCKET', 'my-nasdaq-stock-processed-2026-430970051812-ap-southeast-1-an')
QUARANTINE_BUCKET = os.environ.get('QUARANTINE_BUCKET', PROCESSED_BUCKET)
CLEANSED_BUCKET = os.environ.get('CLEANSED_BUCKET', PROCESSED_BUCKET)

# S3 Prefixes
RAW_PREFIX = os.environ.get('RAW_PREFIX', 'raw/')
PROCESSED_PREFIX = os.environ.get('PROCESSED_PREFIX', 'processed/')
QUARANTINE_PREFIX = os.environ.get('QUARANTINE_PREFIX', 'quarantine/')
CLEANSED_PREFIX = os.environ.get('CLEANSED_PREFIX', 'cleansed/')

# Pipeline B – Daily Increment
# Vùng đệm tạm thời theo ngày: cleansed_daily/YYYY-MM-DD/
# Quality Gate ghi vào đây; Daily ETL Lambda đọc từ đây rồi xóa đi.
CLEANSED_DAILY_PREFIX = os.environ.get('CLEANSED_DAILY_PREFIX', 'cleansed_daily/')

# Prefix lưu báo cáo chất lượng dữ liệu
REPORT_PREFIX = os.environ.get('REPORT_PREFIX', 'reports/')

# Pipeline B – Daily Collector (Step 0)
# S3 location của file JSON chứa danh sách ticker cần theo dõi
# Format JSON: {"tickers": ["AAPL", "MSFT", ...]}
TICKERS_CONFIG_BUCKET = os.environ.get('TICKERS_CONFIG_BUCKET', PROCESSED_BUCKET)
TICKERS_S3_KEY = os.environ.get('TICKERS_S3_KEY', 'config/tickers.json')

# Fan-out Architecture (SQS)
# URL của SQS Queue mà Producer gửi messages vào
SQS_QUEUE_URL = os.environ.get('SQS_QUEUE_URL', '')

# Số tickers mỗi SQS message / Lambda Consumer invocation
CHUNK_SIZE = int(os.environ.get('CHUNK_SIZE', '100'))