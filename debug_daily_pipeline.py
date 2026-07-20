import argparse
import json
import sys
from datetime import datetime, timedelta, timezone

import boto3
import yfinance as yf

# Config — đọc từ biến môi trường hoặc fallback sang giá trị mặc định
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from config import (
    RAW_BUCKET,
    RAW_PREFIX,
    CLEANSED_BUCKET,
    CLEANSED_DAILY_PREFIX,
    PROCESSED_BUCKET,
    TICKERS_CONFIG_BUCKET,
    TICKERS_S3_KEY,
    SQS_QUEUE_URL,
)

s3 = boto3.client("s3")
sqs = boto3.client("sqs")

SEP = "=" * 65


def check_1_producer_logs():
    """Kiểm tra Producer Lambda có được EventBridge trigger không."""
    print(f"\n{SEP}")
    print("🔍 [CHECK 1] Producer Lambda — CloudWatch Logs")
    print(SEP)
    logs = boto3.client("logs")
    log_group = "/aws/lambda/lambda_collector_producer"
    try:
        streams = logs.describe_log_streams(
            logGroupName=log_group,
            orderBy="LastEventTime",
            descending=True,
            limit=3,
        )
        for s in streams.get("logStreams", []):
            ts = s.get("lastEventTimestamp", 0) / 1000
            last_time = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            print(f"  ✅ Log stream: {s['logStreamName']}")
            print(f"     Last event: {last_time}")
    except logs.exceptions.ResourceNotFoundException:
        print(f"  ❌ Log group '{log_group}' KHÔNG TỒN TẠI → Producer chưa từng được gọi!")
        print("     → Kiểm tra EventBridge Rule đã enabled chưa?")
    except Exception as e:
        print(f"  ⚠️  Lỗi khi đọc CloudWatch: {e}")


def check_2_sqs_config():
    """Kiểm tra SQS Queue URL có được set không và queue có message không."""
    print(f"\n{SEP}")
    print("🔍 [CHECK 2] SQS Queue URL & Configuration")
    print(SEP)
    if not SQS_QUEUE_URL:
        print("  ❌ SQS_QUEUE_URL = TRỐNG!")
        print("     → Vào Lambda Console → lambda_collector_producer → Environment variables")
        print("     → Set SQS_QUEUE_URL = https://sqs.<region>.amazonaws.com/<account-id>/<queue-name>")
        return

    print(f"  ✅ SQS_QUEUE_URL = {SQS_QUEUE_URL}")
    try:
        attrs = sqs.get_queue_attributes(
            QueueUrl=SQS_QUEUE_URL,
            AttributeNames=["ApproximateNumberOfMessages", "ApproximateNumberOfMessagesNotVisible"],
        )
        a = attrs["Attributes"]
        print(f"  📬 Messages visible (chờ xử lý)  : {a.get('ApproximateNumberOfMessages', '?')}")
        print(f"  📭 Messages in-flight (đang xử lý): {a.get('ApproximateNumberOfMessagesNotVisible', '?')}")
    except Exception as e:
        print(f"  ⚠️  Không đọc được SQS attributes: {e}")


def check_3_tickers_config():
    """Kiểm tra file tickers.json có trên S3 không."""
    print(f"\n{SEP}")
    print("🔍 [CHECK 3] Tickers Config trên S3")
    print(SEP)
    try:
        resp = s3.get_object(Bucket=TICKERS_CONFIG_BUCKET, Key=TICKERS_S3_KEY)
        content = json.loads(resp["Body"].read().decode())
        tickers = content.get("tickers", [])
        print(f"  ✅ s3://{TICKERS_CONFIG_BUCKET}/{TICKERS_S3_KEY}")
        print(f"     Số lượng tickers: {len(tickers)}")
        print(f"     Mẫu 5 tickers: {tickers[:5]}")
    except s3.exceptions.NoSuchKey:
        print(f"  ❌ File KHÔNG TỒN TẠI: s3://{TICKERS_CONFIG_BUCKET}/{TICKERS_S3_KEY}")
        print("     → Chạy: python upload_tickers_config.py")
    except Exception as e:
        print(f"  ❌ Lỗi: {e}")


def check_4_yfinance(ticker: str, trade_date: str):
    """Kiểm tra yfinance có trả về data cho ngày này không."""
    print(f"\n{SEP}")
    print(f"🔍 [CHECK 4] yfinance Download — ticker={ticker}, date={trade_date}")
    print(SEP)

    # Kiểm tra ngày có phải weekday không
    dt = datetime.strptime(trade_date, "%Y-%m-%d")
    day_name = dt.strftime("%A")
    if dt.weekday() >= 5:  # 5=Sat, 6=Sun
        print(f"  ⚠️  {trade_date} là {day_name} (cuối tuần) → Thị trường ĐÓNG cửa!")
        print("     yfinance sẽ trả về DataFrame rỗng → Đây có thể là nguyên nhân chính!")
    else:
        print(f"  ✅ {trade_date} là {day_name} (ngày giao dịch)")

    end_date = (dt + timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        raw = yf.download(
            tickers=ticker,
            start=trade_date,
            end=end_date,
            auto_adjust=False,
            progress=False,
            threads=False,
        )
        if raw is None or raw.empty:
            print(f"  ❌ yfinance trả về EMPTY DataFrame cho {ticker} ngày {trade_date}")
            print("     Nguyên nhân có thể: ngày nghỉ, ticker không hợp lệ, hoặc rate limit")
        else:
            print(f"  ✅ yfinance OK: {len(raw)} dòng")
            print(f"     Columns: {list(raw.columns)}")
            print(f"     Data:\n{raw.to_string()}")
    except Exception as e:
        print(f"  ❌ yfinance exception: {e}")


def check_5_s3_raw(trade_date: str):
    """Kiểm tra xem có file raw nào trên S3 cho ngày này không."""
    print(f"\n{SEP}")
    print(f"🔍 [CHECK 5] S3 Raw Files — s3://{RAW_BUCKET}/{RAW_PREFIX}{trade_date}/")
    print(SEP)
    prefix = f"{RAW_PREFIX}{trade_date}/"
    try:
        resp = s3.list_objects_v2(Bucket=RAW_BUCKET, Prefix=prefix)
        contents = resp.get("Contents", [])
        if not contents:
            print(f"  ❌ KHÔNG CÓ file nào tại s3://{RAW_BUCKET}/{prefix}")
            print("     → Consumer Lambda chưa upload hoặc đã thất bại")
        else:
            print(f"  ✅ Tìm thấy {len(contents)} file(s):")
            for obj in contents[:10]:
                size_kb = obj["Size"] / 1024
                print(f"     {obj['Key']}  ({size_kb:.1f} KB)")
            if len(contents) > 10:
                print(f"     ... và {len(contents) - 10} file khác")
    except Exception as e:
        print(f"  ❌ Lỗi list S3: {e}")


def check_6_s3_event_notification():
    """Kiểm tra S3 Event Notification có cấu hình không."""
    print(f"\n{SEP}")
    print(f"🔍 [CHECK 6] S3 Event Notification — bucket: {RAW_BUCKET}")
    print(SEP)
    try:
        resp = s3.get_bucket_notification_configuration(Bucket=RAW_BUCKET)
        # Xóa ResponseMetadata để in gọn
        resp.pop("ResponseMetadata", None)
        if not any(resp.get(k) for k in ["LambdaFunctionConfigurations", "QueueConfigurations", "TopicConfigurations"]):
            print("  ❌ KHÔNG CÓ Event Notification nào được cấu hình!")
            print("     → Vào S3 Console → RAW_BUCKET → Properties → Event notifications")
            print("     → Tạo notification: Event type = s3:ObjectCreated:*")
            print("     → Destination = Lambda → lambda_quality_gate")
        else:
            lambdas = resp.get("LambdaFunctionConfigurations", [])
            print(f"  ✅ Tìm thấy {len(lambdas)} Lambda notification(s):")
            for cfg in lambdas:
                print(f"     ARN   : {cfg.get('LambdaFunctionArn', '?')}")
                print(f"     Events: {cfg.get('Events', [])}")
                print(f"     Filter: {cfg.get('Filter', {})}")
    except Exception as e:
        print(f"  ❌ Lỗi đọc S3 notification config: {e}")


def check_7_s3_cleansed(trade_date: str):
    """Kiểm tra vùng đệm cleansed_daily có dữ liệu không."""
    print(f"\n{SEP}")
    print(f"🔍 [CHECK 7] S3 Cleansed Buffer — s3://{CLEANSED_BUCKET}/{CLEANSED_DAILY_PREFIX}{trade_date}/")
    print(SEP)
    prefix = f"{CLEANSED_DAILY_PREFIX}{trade_date}/"
    try:
        resp = s3.list_objects_v2(Bucket=CLEANSED_BUCKET, Prefix=prefix)
        contents = resp.get("Contents", [])
        if not contents:
            print(f"  ❌ KHÔNG CÓ file nào tại s3://{CLEANSED_BUCKET}/{prefix}")
            print("     → Quality Gate Lambda chưa chạy hoặc thất bại")
            print("     → Kiểm tra CloudWatch logs: /aws/lambda/lambda_quality_gate")
        else:
            print(f"  ✅ Tìm thấy {len(contents)} file(s) sạch trong vùng đệm")
    except Exception as e:
        print(f"  ❌ Lỗi: {e}")


def check_8_consumer_logs(trade_date: str):
    """Kiểm tra Consumer Lambda logs."""
    print(f"\n{SEP}")
    print("🔍 [CHECK 8] Consumer Lambda — CloudWatch Logs")
    print(SEP)
    logs = boto3.client("logs")
    log_group = "/aws/lambda/lambda_daily_collector"
    try:
        # Tính thời gian khoảng 24h xung quanh trade_date
        date_obj = datetime.strptime(trade_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        start_ms = int(date_obj.timestamp() * 1000)
        end_ms = int((date_obj + timedelta(hours=4)).timestamp() * 1000)

        events = logs.filter_log_events(
            logGroupName=log_group,
            startTime=start_ms,
            endTime=end_ms,
            filterPattern=f'"{trade_date}"',
            limit=20,
        )
        log_events = events.get("events", [])
        if not log_events:
            print(f"  ⚠️  Không tìm thấy log nào có '{trade_date}' trong khoảng thời gian đó")
            print("     → Có thể Consumer không nhận được SQS message cho ngày này")
        else:
            print(f"  ✅ Tìm thấy {len(log_events)} log event(s) có '{trade_date}':")
            for ev in log_events[:10]:
                ts = datetime.fromtimestamp(ev["timestamp"] / 1000, tz=timezone.utc)
                print(f"     [{ts.strftime('%H:%M:%S')}] {ev['message'][:120]}")
    except logs.exceptions.ResourceNotFoundException:
        print(f"  ❌ Log group '{log_group}' KHÔNG TỒN TẠI → Consumer chưa từng được gọi!")
    except Exception as e:
        print(f"  ⚠️  Lỗi đọc CloudWatch: {e}")


def print_summary(trade_date: str):
    """In tóm tắt và hướng dẫn fix."""
    print(f"\n{SEP}")
    print("📋 HƯỚNG DẪN XỬ LÝ THEO THỨ TỰ ƯU TIÊN")
    print(SEP)
    print("""
  1. Nếu CHECK 4 báo 'cuối tuần' → Đây là nguyên nhân chính.
     yfinance trả về empty → upload lên S3 bị skip → không có data.
     FIX: Thêm điều kiện weekday check vào Producer hoặc Consumer.

  2. Nếu CHECK 1 không có log → EventBridge không trigger Producer.
     FIX: AWS Console → EventBridge → Rules → Bật rule / kiểm tra cron expression.

  3. Nếu CHECK 2 báo SQS_QUEUE_URL trống → Producer sẽ raise exception.
     FIX: Set env var SQS_QUEUE_URL trên Lambda Console.

  4. Nếu CHECK 5 có file raw nhưng CHECK 7 không có cleansed → S3 Event Notification lỗi.
     FIX: CHECK 6 để xem notification đã cấu hình chưa.

  5. Nếu CHECK 5 không có file raw → Consumer không upload được.
     FIX: Xem CHECK 8 (Consumer logs) để tìm exception.

  Chạy lại thủ công cho ngày cụ thể:
    python src/lambda_collector_producer.py --test --date {date}
    python src/lambda_daily_collector.py --test --date {date} --tickers AAPL,MSFT,GOOGL
""".format(date=trade_date))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Debug pipeline daily S3 — tìm nguyên nhân không có dữ liệu raw"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Ngày cần kiểm tra (YYYY-MM-DD). Mặc định: hôm qua.",
    )
    parser.add_argument(
        "--ticker",
        type=str,
        default="AAPL",
        help="Ticker để test yfinance download (mặc định: AAPL).",
    )
    parser.add_argument(
        "--check-all",
        action="store_true",
        help="Chạy tất cả các bước kiểm tra (mặc định: chỉ chạy các check cơ bản).",
    )
    args = parser.parse_args()

    # Xác định trade_date
    if args.date:
        trade_date = args.date
    else:
        trade_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"\n{'#' * 65}")
    print(f"  DEBUG DAILY PIPELINE — trade_date = {trade_date}")
    print(f"{'#' * 65}")

    # Các check cơ bản (luôn chạy)
    check_3_tickers_config()
    check_4_yfinance(args.ticker, trade_date)
    check_5_s3_raw(trade_date)
    check_7_s3_cleansed(trade_date)

    # Các check cần AWS CloudWatch/SQS permissions (--check-all)
    if args.check_all:
        check_1_producer_logs()
        check_2_sqs_config()
        check_6_s3_event_notification()
        check_8_consumer_logs(trade_date)

    print_summary(trade_date)
