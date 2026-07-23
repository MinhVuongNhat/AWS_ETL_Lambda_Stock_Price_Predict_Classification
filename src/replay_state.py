import json
import os
from datetime import datetime, timedelta
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from logger import get_logger

logger = get_logger(__name__)

# US Market Holidays 2025–2026
US_MARKET_HOLIDAYS = {
    # 2025
    "2025-01-01",  # New Year's Day
    "2025-01-20",  # MLK Day
    "2025-02-17",  # Presidents' Day
    "2025-04-18",  # Good Friday
    "2025-05-26",  # Memorial Day
    "2025-07-04",  # Independence Day
    "2025-09-01",  # Labor Day
    "2025-11-27",  # Thanksgiving
    "2025-11-28",  # Black Friday (early close — bỏ qua)
    "2025-12-25",  # Christmas
    # 2026
    "2026-01-01",  # New Year's Day
    "2026-01-19",  # MLK Day
    "2026-02-16",  # Presidents' Day
    "2026-04-03",  # Good Friday
    "2026-05-25",  # Memorial Day
    "2026-07-03",  # Independence Day (observed)
    "2026-09-07",  # Labor Day
    "2026-11-26",  # Thanksgiving
    "2026-11-27",  # Black Friday (early close — bỏ qua)
    "2026-12-25",  # Christmas
}

DEFAULT_STATE = {
    "replay_start_date": "2025-01-02",
    "replay_end_date": "2026-07-18",
    "current_date": "2025-01-02",
    "interval_minutes": 1,
    "status": "running",       # running | paused | completed
    "last_run_utc": None,
    "total_days_replayed": 0,
}


class ReplayStateManager:
    """
    Quản lý trạng thái replay — đọc/ghi qua S3 hoặc local file.
    """

    def __init__(
        self,
        bucket: Optional[str] = None,
        key: Optional[str] = None,
        local_path: Optional[str] = None,
    ):
        self._local_path = local_path
        self._bucket = bucket
        self._key = key

        if local_path:
            self._s3 = None
            logger.info(f"ReplayStateManager → LOCAL mode: {local_path}")
        else:
            self._s3 = boto3.client("s3")
            logger.info(f"ReplayStateManager → S3 mode: s3://{bucket}/{key}")

    # State I/O
    def get_state(self) -> dict:
        """Đọc trạng thái hiện tại. Trả về DEFAULT_STATE nếu chưa tồn tại."""
        if self._local_path:
            return self._read_local()
        return self._read_s3()

    def save_state(self, state: dict) -> None:
        """Ghi trạng thái mới."""
        if self._local_path:
            self._write_local(state)
        else:
            self._write_s3(state)

    def _read_local(self) -> dict:
        if not os.path.exists(self._local_path):
            logger.info("State file chưa tồn tại local — dùng DEFAULT_STATE")
            return DEFAULT_STATE.copy()
        with open(self._local_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_local(self, state: dict) -> None:
        os.makedirs(os.path.dirname(self._local_path) or ".", exist_ok=True)
        with open(self._local_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def _read_s3(self) -> dict:
        try:
            response = self._s3.get_object(Bucket=self._bucket, Key=self._key)
            return json.loads(response["Body"].read().decode("utf-8-sig"))
        except ClientError as e:
            if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
                logger.info("State file chưa tồn tại trên S3 — dùng DEFAULT_STATE")
                return DEFAULT_STATE.copy()
            raise

    def _write_s3(self, state: dict) -> None:
        self._s3.put_object(
            Bucket=self._bucket,
            Key=self._key,
            Body=json.dumps(state, indent=2, ensure_ascii=False).encode("utf-8"),
            ContentType="application/json",
        )

    # Trading Day Logic
    @staticmethod
    def is_trading_day(date_str: str) -> bool:
        """Trả về True nếu date_str là ngày giao dịch (không phải weekend/holiday)."""
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        if dt.weekday() >= 5:  # Saturday=5, Sunday=6
            return False
        return date_str not in US_MARKET_HOLIDAYS

    @staticmethod
    def next_trading_day(date_str: str, max_lookahead: int = 14) -> Optional[str]:
        """
        Tìm ngày giao dịch tiếp theo sau date_str.
        Trả về None nếu không tìm được trong max_lookahead ngày.
        """
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        for _ in range(max_lookahead):
            dt += timedelta(days=1)
            candidate = dt.strftime("%Y-%m-%d")
            if ReplayStateManager.is_trading_day(candidate):
                return candidate
        return None

    @staticmethod
    def count_trading_days_remaining(current_date: str, end_date: str) -> int:
        """Đếm số ngày giao dịch còn lại từ current_date đến end_date."""
        count = 0
        dt = datetime.strptime(current_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        while dt <= end_dt:
            if ReplayStateManager.is_trading_day(dt.strftime("%Y-%m-%d")):
                count += 1
            dt += timedelta(days=1)
        return count

    # State Transitions

    def advance(self) -> dict:
        """
        Advance current_date → ngày giao dịch tiếp theo.
        Cập nhật total_days_replayed và last_run_utc.
        Nếu đã hết data → set status = 'completed'.
        Trả về state mới.
        """
        state = self.get_state()
        current = state["current_date"]
        end = state["replay_end_date"]

        next_day = self.next_trading_day(current)

        if next_day is None or next_day > end:
            state["status"] = "completed"
            logger.info(f"🏁 Replay hoàn tất! Ngày cuối cùng đã replay: {current}")
        else:
            state["current_date"] = next_day
            state["total_days_replayed"] = state.get("total_days_replayed", 0) + 1
            logger.info(
                f"⏩ Advance: {current} → {next_day} "
                f"(đã replay: {state['total_days_replayed']} ngày)"
            )

        state["last_run_utc"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.save_state(state)
        return state

    def pause(self) -> dict:
        """Tạm dừng replay. Trả về state sau khi pause."""
        state = self.get_state()
        if state["status"] == "running":
            state["status"] = "paused"
            self.save_state(state)
            logger.info("⏸ Replay đã tạm dừng.")
        else:
            logger.warning(f"Không thể pause — status hiện tại: {state['status']}")
        return state

    def resume(self) -> dict:
        """Tiếp tục replay từ trạng thái paused. Trả về state sau khi resume."""
        state = self.get_state()
        if state["status"] == "paused":
            state["status"] = "running"
            self.save_state(state)
            logger.info(f"▶️ Replay tiếp tục từ ngày: {state['current_date']}")
        else:
            logger.warning(f"Không thể resume — status hiện tại: {state['status']}")
        return state

    def initialize(
        self,
        start_date: str = "2025-01-02",
        end_date: str = "2026-07-18",
        interval_minutes: int = 1,
        overwrite: bool = False,
    ) -> dict:
        """
        Khởi tạo state file mới. Chỉ ghi nếu chưa tồn tại hoặc overwrite=True.
        Trả về state đã ghi.
        """
        existing = self.get_state()
        # Kiểm tra xem đây có phải DEFAULT_STATE không (chưa khởi tạo bao giờ)
        is_fresh = existing.get("total_days_replayed", 0) == 0 and \
                   existing.get("status") == "running" and \
                   existing.get("current_date") == DEFAULT_STATE["current_date"]

        if not overwrite and not is_fresh:
            logger.info(
                f"State đã tồn tại (current_date={existing['current_date']}, "
                f"status={existing['status']}). Dùng --overwrite để reset."
            )
            return existing

        # Tìm ngày giao dịch đầu tiên >= start_date
        first_day = start_date if self.is_trading_day(start_date) else self.next_trading_day(
            (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        )

        state = {
            "replay_start_date": start_date,
            "replay_end_date": end_date,
            "current_date": first_day,
            "interval_minutes": interval_minutes,
            "status": "running",
            "last_run_utc": None,
            "total_days_replayed": 0,
        }
        self.save_state(state)
        logger.info(
            f"✅ State khởi tạo: {start_date} → {end_date}, "
            f"bắt đầu từ {first_day}, interval={interval_minutes} phút"
        )
        return state

    def get_summary(self) -> dict:
        """Trả về dict tóm tắt tiến độ replay (dùng cho dashboard/monitor)."""
        state = self.get_state()
        current = state.get("current_date", "N/A")
        end = state.get("replay_end_date", "N/A")

        try:
            remaining = self.count_trading_days_remaining(current, end)
        except Exception:
            remaining = -1

        return {
            "status": state.get("status", "unknown"),
            "current_date": current,
            "replay_start_date": state.get("replay_start_date"),
            "replay_end_date": end,
            "total_days_replayed": state.get("total_days_replayed", 0),
            "trading_days_remaining": remaining,
            "last_run_utc": state.get("last_run_utc"),
            "interval_minutes": state.get("interval_minutes", 1),
        }
