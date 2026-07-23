import json
import math
from datetime import datetime, timezone

import boto3

from config import (
    CHUNK_SIZE,
    SQS_QUEUE_URL,
    TICKERS_CONFIG_BUCKET,
    TICKERS_S3_KEY,
    REPLAY_STATE_BUCKET,
    REPLAY_STATE_KEY,
)
from logger import get_logger
from replay_state import ReplayStateManager

logger = get_logger(__name__)

s3_client = boto3.client("s3")
sqs_client = boto3.client("sqs")

# Helpers (tái sử dụng từ lambda_collector_producer.py)
def load_tickers_from_s3() -> list[str]:
    """Đọc danh sách ticker từ S3 config/tickers.json."""
    logger.info(f"Tải danh sách ticker từ s3://{TICKERS_CONFIG_BUCKET}/{TICKERS_S3_KEY}")
    response = s3_client.get_object(Bucket=TICKERS_CONFIG_BUCKET, Key=TICKERS_S3_KEY)
    content = response["Body"].read().decode("utf-8")
    data = json.loads(content)
    tickers = data.get("tickers", [])
    if not tickers:
        raise ValueError(f"Danh sách ticker rỗng trong s3://{TICKERS_CONFIG_BUCKET}/{TICKERS_S3_KEY}")
    logger.info(f"Đã tải {len(tickers)} ticker.")
    return tickers


def chunked(lst: list, size: int):
    """Chia list thành các sub-list kích thước size."""
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


def send_chunks_to_sqs(chunks: list[list[str]], trade_date: str, queue_url: str) -> int:
    """
    Gửi danh sách chunks vào SQS.
    Mỗi chunk = 1 SQS message: {"trade_date": "...", "tickers": [...]}
    Trả về tổng số messages đã gửi thành công.
    """
    SQS_BATCH_LIMIT = 10
    total_sent = 0
    total_chunks = len(chunks)
    num_batches = math.ceil(total_chunks / SQS_BATCH_LIMIT)

    logger.info(f"Gửi {total_chunks} chunks vào SQS ({num_batches} batch)...")

    for batch_idx, batch_start in enumerate(range(0, total_chunks, SQS_BATCH_LIMIT)):
        batch = chunks[batch_start : batch_start + SQS_BATCH_LIMIT]
        entries = [
            {
                "Id": str(batch_start + i),
                "MessageBody": json.dumps({
                    "trade_date": trade_date,
                    "tickers": chunk,
                    "chunk_index": batch_start + i,
                    "total_chunks": total_chunks,
                }),
            }
            for i, chunk in enumerate(batch)
        ]

        response = sqs_client.send_message_batch(QueueUrl=queue_url, Entries=entries)

        failed = response.get("Failed", [])
        if failed:
            raise RuntimeError(f"SQS SendMessageBatch thất bại: {failed}")

        sent_count = len(response.get("Successful", []))
        total_sent += sent_count
        logger.info(f"  ✅ Batch {batch_idx+1}/{num_batches}: {sent_count} messages")

    return total_sent

# Lambda Handler
def lambda_handler(event, context):
    """
    [Replay Producer]
    Triggered bởi EventBridge Scheduler mỗi 1 phút.

    Event hỗ trợ:
      {"action": "pause"}   → Tạm dừng replay
      {"action": "resume"}  → Tiếp tục replay
      {}                    → Chạy bình thường (replay 1 ngày)
    """
    try:
        logger.info("🚀 REPLAY PRODUCER KHỞI ĐỘNG...")

        state_mgr = ReplayStateManager(
            bucket=REPLAY_STATE_BUCKET,
            key=REPLAY_STATE_KEY,
        )

        # Xử lý action điều khiển từ event
        action = event.get("action") if isinstance(event, dict) else None
        if action == "pause":
            state = state_mgr.pause()
            return {"statusCode": 200, "body": "Replay paused", "state": state}
        if action == "resume":
            state = state_mgr.resume()
            return {"statusCode": 200, "body": "Replay resumed", "state": state}

        # Kiểm tra trạng thái hiện tại
        state = state_mgr.get_state()
        status = state.get("status", "running")

        if status == "paused":
            logger.info("⏸ Replay đang tạm dừng. Producer bỏ qua lần chạy này.")
            return {
                "statusCode": 200,
                "body": "Replay paused — skipped",
                "current_date": state.get("current_date"),
                "skipped": True,
            }

        if status == "completed":
            logger.info("✅ Replay đã hoàn tất toàn bộ dữ liệu.")
            return {
                "statusCode": 200,
                "body": "Replay completed",
                "current_date": state.get("current_date"),
                "skipped": True,
            }

        trade_date = state["current_date"]
        logger.info(f"🎯 Replay ngày: {trade_date} (đã replay: {state.get('total_days_replayed', 0)} ngày)")

        # Validate SQS URL
        if not SQS_QUEUE_URL:
            raise ValueError("SQS_QUEUE_URL chưa được cấu hình.")

        # Tải tickers và gửi SQS
        tickers = load_tickers_from_s3()
        chunks = list(chunked(tickers, CHUNK_SIZE))
        logger.info(f"Chia {len(tickers)} tickers → {len(chunks)} chunks (CHUNK_SIZE={CHUNK_SIZE})")

        total_sent = send_chunks_to_sqs(chunks, trade_date, SQS_QUEUE_URL)

        # Advance state → ngày tiếp theo
        new_state = state_mgr.advance()
        next_date = new_state.get("current_date")
        new_status = new_state.get("status")

        summary = (
            f"Replay Producer: {trade_date} → {total_sent} SQS messages gửi | "
            f"Ngày tiếp theo: {next_date} | Status: {new_status}"
        )
        logger.info(f"🎉 {summary}")

        return {
            "statusCode": 200,
            "body": summary,
            "trade_date": trade_date,
            "next_date": next_date,
            "total_tickers": len(tickers),
            "total_chunks": len(chunks),
            "total_messages_sent": total_sent,
            "status": new_status,
        }

    except Exception as e:
        logger.error(f"❌ Lỗi nghiêm trọng tại Replay Producer: {str(e)}")
        raise

# Local test runner
if __name__ == "__main__":
    import argparse
    import sys
    import os

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

    parser = argparse.ArgumentParser(description="Local test runner cho Replay Producer")
    parser.add_argument("--action", choices=["run", "pause", "resume"], default="run")
    args = parser.parse_args()

    event = {}
    if args.action in ("pause", "resume"):
        event["action"] = args.action

    result = lambda_handler(event, None)
    print("\n=== KẾT QUẢ ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
