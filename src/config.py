import os

# S3 Configuration
RAW_BUCKET = os.environ.get('RAW_BUCKET', 'my-finance-raw-bucket')
PROCESSED_BUCKET = os.environ.get('PROCESSED_BUCKET', 'my-finance-processed-bucket')

# S3 Prefixes
RAW_PREFIX = os.environ.get('RAW_PREFIX', 'raw/')
PROCESSED_PREFIX = os.environ.get('PROCESSED_PREFIX', 'processed/')