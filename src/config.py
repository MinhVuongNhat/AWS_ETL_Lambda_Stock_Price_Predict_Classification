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