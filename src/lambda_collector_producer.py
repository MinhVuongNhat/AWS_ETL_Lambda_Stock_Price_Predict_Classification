import json
import math
from datetime import datetime, timedelta, timezone
from typing import Optional

import boto3

from config import (
    CHUNK_SIZE,
    SQS_QUEUE_URL,
    TICKERS_CONFIG_BUCKET,
    TICKERS_S3_KEY,
)
from logger import get_logger

logger = get_logger(__name__)

s3_client = boto3.client("s3")
sqs_client = boto3.client("sqs")

# Helper: Tải danh sách ticker từ S3
def load_tickers_from_s3() -> list[str]:
    """
    Đọc file JSON trên S3 và trả về danh sách ticker.
    Format JSON: {"tickers": ["AAPL", "MSFT", ...]}
    """
    logger.info(f"Đang tải danh sách ticker từ s3://{TICKERS_CONFIG_BUCKET}/{TICKERS_S3_KEY}")
    response = s3_client.get_object(Bucket=TICKERS_CONFIG_BUCKET, Key=TICKERS_S3_KEY)
    content = response["Body"].read().decode("utf-8")
    data = json.loads(content)
    tickers = data.get("tickers", [])
    if not tickers:
        raise ValueError(f"Danh sách ticker rỗng trong s3://{TICKERS_CONFIG_BUCKET}/{TICKERS_S3_KEY}")
    logger.info(f"Đã tải {len(tickers)} ticker.")
    return tickers

# Helper: Chia list thành các chunks
def chunked(lst: list, size: int):
    """Yield các sub-list kích thước `size` từ list gốc."""
    for i in range(0, len(lst), size):
        yield lst[i : i + size]

# Helper: Kiểm tra ngày giao dịch hợp lệ
US_MARKET_HOLIDAYS_2026 = {
    "2026-01-01",  # New Year's Day
    "2026-01-19",  # MLK Day
    "2026-02-16",  # Presidents' Day
    "2026-04-03",  # Good Friday
    "2026-05-25",  # Memorial Day
    "2026-07-03",  # Independence Day (observed)
    "2026-09-07",  # Labor Day
    "2026-11-26",  # Thanksgiving
    "2026-11-27",  # Black Friday (early close — bỏ qua để an toàn)
    "2026-12-25",  # Christmas
}

def is_trading_day(trade_date: str) -> tuple[bool, str]:
    """
    Kiểm tra xem trade_date có phải ngày giao dịch hợp lệ không.
    Trả về (True/False, lý_do).
    """
    dt = datetime.strptime(trade_date, "%Y-%m-%d")
    weekday = dt.weekday()  # 0=Mon ... 4=Fri, 5=Sat, 6=Sun

    if weekday == 5:
        return False, f"{trade_date} la Thu Bay — thi truong dong cua"
    if weekday == 6:
        return False, f"{trade_date} la Chu Nhat — thi truong dong cua"
    if trade_date in US_MARKET_HOLIDAYS_2026:
        return False, f"{trade_date} la ngay le thi truong My (US_MARKET_HOLIDAYS_2026)"

    return True, "Ngay giao dich hop le"

# Helper: Gửi một batch messages vào SQS
def send_chunks_to_sqs(chunks: list[list[str]], trade_date: str, queue_url: str) -> int:
    """
    Gửi danh sách chunks vào SQS.
    Mỗi chunk = 1 SQS message với body: {"trade_date": "...", "tickers": [...]}
    Trả về tổng số messages đã gửi thành công.
    """
    SQS_BATCH_LIMIT = 10  # SQS giới hạn 10 messages mỗi lần SendMessageBatch

    total_sent = 0
    total_chunks = len(chunks)
    num_batches = math.ceil(total_chunks / SQS_BATCH_LIMIT)

    logger.info(
        f"Gửi {total_chunks} chunks vào SQS theo {num_batches} batch "
        f"(mỗi batch tối đa {SQS_BATCH_LIMIT} messages)..."
    )

    for batch_idx, batch_start in enumerate(range(0, total_chunks, SQS_BATCH_LIMIT)):
        batch = chunks[batch_start : batch_start + SQS_BATCH_LIMIT]
        entries = [
            {
                "Id": str(batch_start + i),  # ID duy nhất trong batch
                "MessageBody": json.dumps(
                    {
                        "trade_date": trade_date,
                        "tickers": chunk,
                        "chunk_index": batch_start + i,
                        "total_chunks": total_chunks,
                    }
                ),
            }
            for i, chunk in enumerate(batch)
        ]

        response = sqs_client.send_message_batch(
            QueueUrl=queue_url,
            Entries=entries,
        )

        # Kiểm tra lỗi gửi
        failed = response.get("Failed", [])
        if failed:
            failed_ids = [f["Id"] for f in failed]
            logger.error(f"  ❌ Batch {batch_idx + 1}: {len(failed)} messages thất bại. IDs: {failed_ids}")
            raise RuntimeError(
                f"SQS SendMessageBatch thất bại cho {len(failed)} messages: {failed}"
            )

        sent_count = len(response.get("Successful", []))
        total_sent += sent_count
        logger.info(f"  ✅ Batch {batch_idx + 1}/{num_batches}: Gửi thành công {sent_count} messages.")

    return total_sent

# Lambda Handler
def lambda_handler(event, context):
    """
    [Pipeline B - Daily Collector - Producer]
    Triggered bởi EventBridge Scheduler lúc 00:00 UTC mỗi ngày.
    Chia danh sách tickers thành chunks và gửi vào SQS để Consumer xử lý song song.
    """
    try:
        logger.info("🚀 KHỞI ĐỘNG DAILY COLLECTOR PRODUCER...")

        # Validate SQS Queue URL
        if not SQS_QUEUE_URL:
            raise ValueError(
                "Biến môi trường SQS_QUEUE_URL chưa được cấu hình. "
                "Vui lòng set env var này trên Lambda Console."
            )

        # Bước 1: Xác định ngày giao dịch cần tải
        # Lambda chạy lúc 00:00 UTC → ngày giao dịch là ngày hôm trước (UTC)
        trade_date: Optional[str] = event.get("trade_date") if isinstance(event, dict) else None
        if trade_date:
            logger.info(f"Override trade_date tu event: {trade_date}")
        else:
            now_utc = datetime.now(timezone.utc)
            trade_date = (now_utc - timedelta(days=1)).strftime("%Y-%m-%d")
        logger.info(f"Ngay giao dich can tai: {trade_date}")

        # Bước 1b: Kiểm tra ngày giao dịch hợp lệ
        # Nếu là cuối tuần / ngày lễ → dừng ngay, KHÔNG gửi SQS
        force_run: bool = bool(event.get("force", False)) if isinstance(event, dict) else False
        tradeable, reason = is_trading_day(trade_date)
        if not tradeable and not force_run:
            msg = (
                f"No-op: {reason}. Producer dung lai, khong gui SQS. "
                f"De bypass, truyen event={{\"force\": true, \"trade_date\": \"{trade_date}\"}}."
            )
            logger.info(f"Thi truong nghi: {msg}")
            return {
                "statusCode": 200,
                "body": msg,
                "trade_date": trade_date,
                "total_tickers": 0,
                "total_chunks": 0,
                "total_messages_sent": 0,
                "skipped": True,
            }
        if force_run and not tradeable:
            logger.info(f"force=true: Bo qua weekend/holiday check cho {trade_date}. Tiep tuc...")

        # Bước 2: Tải danh sách ticker từ S3
        tickers = load_tickers_from_s3()

        # Bước 3: Chia thành các chunks
        chunks = list(chunked(tickers, CHUNK_SIZE))
        logger.info(
            f"Chia {len(tickers)} tickers thành {len(chunks)} chunks "
            f"(CHUNK_SIZE={CHUNK_SIZE})."
        )

        # Bước 4: Gửi tất cả chunks vào SQS
        total_sent = send_chunks_to_sqs(chunks, trade_date, SQS_QUEUE_URL)

        # Bước 5: Tổng kết
        summary = (
            f"Producer hoàn tất cho ngày {trade_date}: "
            f"{len(tickers)} tickers → {len(chunks)} chunks → "
            f"{total_sent} SQS messages đã gửi."
        )
        logger.info(f"🎉 {summary}")

        return {
            "statusCode": 200,
            "body": summary,
            "trade_date": trade_date,
            "total_tickers": len(tickers),
            "total_chunks": len(chunks),
            "total_messages_sent": total_sent,
        }

    except Exception as e:
        logger.error(f"❌ Lỗi nghiêm trọng tại Producer: {str(e)}")
        raise e

# Local test runner
if __name__ == "__main__":
    import argparse
    import os
    import sys

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

    parser = argparse.ArgumentParser(description="Local test runner cho Daily Collector Producer")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Chạy lambda_handler với mock event để kiểm tra local",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Override ngày giao dịch (YYYY-MM-DD). Mặc định: hôm qua.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chỉ load tickers và in thông tin chunks, KHÔNG gửi SQS thật.",
    )
    args = parser.parse_args()

    if args.test:
        if args.dry_run:
            # Dry run: chỉ load và chia chunks, không cần SQS_QUEUE_URL
            print("=== DRY RUN MODE (không gửi SQS) ===")
            tickers = load_tickers_from_s3()
            chunks = list(chunked(tickers, CHUNK_SIZE))
            print(f"Tổng tickers: {len(tickers)}")
            print(f"Chunk size: {CHUNK_SIZE}")
            print(f"Tổng chunks sẽ gửi: {len(chunks)}")
            print(f"Chunk đầu tiên (5 tickers): {chunks[0][:5]}...")
            print(f"Chunk cuối cùng: {chunks[-1][:5]}...")
        else:
            event = {}
            if args.date:
                event["trade_date"] = args.date
            result = lambda_handler(event, None)
            print("\n=== KẾT QUẢ ===")
            print(result)
