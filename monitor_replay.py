import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.replay_state import ReplayStateManager
from config import REPLAY_STATE_BUCKET, REPLAY_STATE_KEY

STATE_FILE_LOCAL = PROJECT_ROOT / "data" / "replay_state.json"

# ANSI Colors (fallback gracefully trên Windows)
try:
    import os as _os
    _os.get_terminal_size()  # Check terminal available
    _COLORS = True
except Exception:
    _COLORS = False

def c(text: str, code: str) -> str:
    if not _COLORS:
        return text
    return f"\033[{code}m{text}\033[0m"

GREEN  = lambda t: c(t, "32")
YELLOW = lambda t: c(t, "33")
RED    = lambda t: c(t, "31")
CYAN   = lambda t: c(t, "36")
BOLD   = lambda t: c(t, "1")
DIM    = lambda t: c(t, "2")


def status_color(status: str) -> str:
    """Trả về status được tô màu."""
    colors = {
        "running":   GREEN,
        "paused":    YELLOW,
        "completed": CYAN,
        "unknown":   RED,
    }
    fn = colors.get(status, RED)
    return fn(status.upper())


def build_progress_bar(replayed: int, remaining: int, width: int = 30) -> str:
    """Tạo thanh tiến độ ASCII."""
    total = replayed + remaining
    if total == 0:
        return "[" + "─" * width + "]"
    filled = int(width * replayed / total)
    bar = "█" * filled + "░" * (width - filled)
    pct = replayed / total * 100
    return f"[{bar}] {pct:.1f}%"


def print_dashboard(summary: dict, mode: str = "local") -> None:
    """In dashboard ra terminal."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = summary.get("status", "unknown")
    current = summary.get("current_date", "N/A")
    start = summary.get("replay_start_date", "N/A")
    end = summary.get("replay_end_date", "N/A")
    replayed = summary.get("total_days_replayed", 0)
    remaining = summary.get("trading_days_remaining", 0)
    last_run = summary.get("last_run_utc") or "Never"
    interval = summary.get("interval_minutes", 1)

    progress = build_progress_bar(replayed, remaining)

    print("\033[2J\033[H", end="")  # Clear screen

    print(BOLD("╔══════════════════════════════════════════════════════╗"))
    print(BOLD("║         📈  STOCK REPLAY MONITOR                    ║"))
    print(BOLD("╚══════════════════════════════════════════════════════╝"))
    print()
    print(f"  {BOLD('Mode')}            : {CYAN(mode.upper())}")
    print(f"  {BOLD('Status')}          : {status_color(status)}")
    print()
    print(f"  {BOLD('Current Date')}    : {CYAN(current)}")
    print(f"  {BOLD('Replay Range')}    : {start}  →  {end}")
    print()
    print(f"  {BOLD('Progress')}        : {progress}")
    print(f"  {BOLD('Days Replayed')}   : {GREEN(str(replayed))}")
    print(f"  {BOLD('Days Remaining')}  : {str(remaining)}")
    print()
    print(f"  {BOLD('Interval')}        : {interval} min/ngày giao dịch")
    print(f"  {BOLD('Last Run (UTC)')}  : {DIM(last_run)}")
    print()
    print(DIM(f"  Cập nhật lúc: {now}"))
    print()

    # Gợi ý lệnh
    if status == "running":
        print(DIM("  💡 Dừng replay: python monitor_replay.py --pause"))
    elif status == "paused":
        print(YELLOW("  ⏸ Replay đang tạm dừng"))
        print(DIM("  💡 Tiếp tục: python monitor_replay.py --resume"))
    elif status == "completed":
        print(GREEN("  🏁 Replay đã hoàn tất!"))

    print(DIM("  ─────────────────────────────────────────────────────"))
    print(DIM("  Nhấn Ctrl+C để thoát"))


def get_state_manager(use_s3: bool) -> ReplayStateManager:
    if use_s3:
        return ReplayStateManager(
            bucket=REPLAY_STATE_BUCKET,
            key=REPLAY_STATE_KEY,
        )
    return ReplayStateManager(local_path=str(STATE_FILE_LOCAL))


def main():
    parser = argparse.ArgumentParser(
        description="Replay Monitor — Theo dõi và điều khiển tiến độ replay",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--s3", action="store_true", help="Dùng state S3 (production). Mặc định: local file")
    parser.add_argument("--pause", action="store_true", help="Tạm dừng replay")
    parser.add_argument("--resume", action="store_true", help="Tiếp tục replay")
    parser.add_argument("--watch", action="store_true", help="Tự động refresh dashboard")
    parser.add_argument("--refresh", type=int, default=10, help="Interval refresh (giây, default=10)")
    parser.add_argument("--json", action="store_true", help="Xuất trạng thái dạng JSON")

    args = parser.parse_args()

    mode = "s3" if args.s3 else "local"
    mgr = get_state_manager(use_s3=args.s3)

    # Lệnh điều khiển
    if args.pause:
        state = mgr.pause()
        print(f"⏸ Replay đã tạm dừng tại ngày: {state.get('current_date')}")
        return

    if args.resume:
        state = mgr.resume()
        print(f"▶️  Replay tiếp tục từ ngày: {state.get('current_date')}")
        return

    # Xuất JSON
    if args.json:
        summary = mgr.get_summary()
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return

    # Dashboard
    if args.watch:
        print(f"Đang theo dõi replay state ({mode.upper()}) — refresh mỗi {args.refresh}s...")
        try:
            while True:
                summary = mgr.get_summary()
                print_dashboard(summary, mode=mode)
                time.sleep(args.refresh)
        except KeyboardInterrupt:
            print("\n\nĐã thoát monitor.")
    else:
        summary = mgr.get_summary()
        print_dashboard(summary, mode=mode)


if __name__ == "__main__":
    main()
