import argparse
import json
import os
import sys
from pathlib import Path

import boto3
from dotenv import load_dotenv

# Load .env để có AWS credentials và bucket config
load_dotenv(Path(__file__).parent / ".env")

TICKERS_CONFIG_BUCKET = os.environ.get(
    "TICKERS_CONFIG_BUCKET",
    "my-nasdaq-stock-processed-2026-430970051812-ap-southeast-1-an"
)
TICKERS_S3_KEY = os.environ.get("TICKERS_S3_KEY", "config/tickers.json")


def upload_tickers(file_path: Path) -> None:
    """Upload tickers JSON lên S3."""
    if not file_path.exists():
        print(f"❌ File không tồn tại: {file_path}")
        sys.exit(1)

    # Validate JSON format
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tickers = data.get("tickers", [])
    if not tickers:
        print("❌ File JSON không có trường 'tickers' hoặc danh sách rỗng.")
        sys.exit(1)

    print(f"✅ File hợp lệ: {len(tickers)} ticker")
    print(f"   Ví dụ: {tickers[:5]}{'...' if len(tickers) > 5 else ''}")

    # Upload
    s3_client = boto3.client("s3")
    s3_client.upload_file(str(file_path), TICKERS_CONFIG_BUCKET, TICKERS_S3_KEY)
    print(f"🎉 Upload thành công: s3://{TICKERS_CONFIG_BUCKET}/{TICKERS_S3_KEY}")


def main():
    parser = argparse.ArgumentParser(description="Upload tickers.json lên S3")
    parser.add_argument(
        "--file",
        type=str,
        default=str(Path(__file__).parent / "tickers.json"),
        help="Đường dẫn tới file tickers JSON (mặc định: ./tickers.json)",
    )
    args = parser.parse_args()
    upload_tickers(Path(args.file))


if __name__ == "__main__":
    main()
