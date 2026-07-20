import argparse
import io
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows terminal UTF-8 encoding
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Config
NASDAQ_TRADED_URL = "http://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt"

# Symbols chứa ký tự đặc biệt thường là warrant, unit, preferred share...
SYMBOL_BLACKLIST_CHARS = set("^/=+.")

# Suffix thường xuất hiện ở warrant (W), rights (R), units (U), preferred (P)
SYMBOL_WARRANT_SUFFIXES = ("W", "R", "U")  # chỉ áp dụng khi len >= 5

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_FILE = PROJECT_ROOT / "tickers.json"

# Parse NASDAQ file
def fetch_nasdaq_traded_file() -> str:
    """Download file danh sách chứng khoán từ nasdaqtrader.com."""
    # Thử HTTPS trước (nhanh hơn và ổn định hơn), fallback về HTTP
    urls = [
        "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt",
        "http://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt",
    ]

    for attempt, url in enumerate(urls, 1):
        try:
            print(f"[{attempt}/{len(urls)}] Đang tải từ: {url}")
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; nasdaq-ticker-refresh/1.0)"},
            )
            with urllib.request.urlopen(req, timeout=60) as response:
                content = response.read().decode("utf-8", errors="replace")
            print(f"   Tai xong ({len(content):,} bytes)")
            return content
        except Exception as e:
            print(f"   Loi khi tai tu {url}: {e}")
            if attempt == len(urls):
                raise RuntimeError(f"Khong the tai file sau {len(urls)} lan thu. Loi cuoi: {e}")


def parse_tickers(
    content: str,
    exclude_etf: bool = False,
    nasdaq_only: bool = False,
    exclude_distressed: bool = False,
) -> list[dict]:
    """
    Phân tích nội dung file pipe-delimited và lọc theo tiêu chí.
    Trả về list[dict] với keys: symbol, name, exchange, is_etf.
    """
    lines = content.splitlines()
    if not lines:
        raise ValueError("File rỗng!")

    # Dòng đầu là header, dòng cuối là footer (File Creation Time: ...)
    header_line = lines[0]
    data_lines = lines[1:]

    # Xác minh header đúng format
    expected_header = "Nasdaq Traded|Symbol|Security Name|Listing Exchange"
    if not header_line.startswith(expected_header):
        raise ValueError(f"Header không khớp! Nhận được: {header_line[:80]}")

    results = []
    skipped_stats = {
        "not_traded": 0,
        "test_issue": 0,
        "etf_excluded": 0,
        "exchange_filtered": 0,
        "distressed": 0,
        "bad_symbol": 0,
        "footer": 0,
    }

    for line in data_lines:
        line = line.strip()
        if not line:
            continue

        parts = line.split("|")
        if len(parts) < 10:
            skipped_stats["footer"] += 1
            continue

        nasdaq_traded = parts[0].strip()
        symbol        = parts[1].strip()
        name          = parts[2].strip()
        exchange      = parts[3].strip()  # Q=NASDAQ, N=NYSE, P=ARCA, Z=BATS
        is_etf        = parts[5].strip()
        test_issue    = parts[7].strip()
        fin_status    = parts[8].strip()  # "" hoặc "N" = bình thường; "D" = deficient

        # Lọc: chỉ lấy ticker đang giao dịch
        if nasdaq_traded != "Y":
            skipped_stats["not_traded"] += 1
            continue

        # Lọc: bỏ test issue
        if test_issue == "Y":
            skipped_stats["test_issue"] += 1
            continue

        # Lọc: bỏ ETF nếu yêu cầu
        if is_etf == "Y" and exclude_etf:
            skipped_stats["etf_excluded"] += 1
            continue

        # Lọc: chỉ lấy sàn NASDAQ (Market Category Q) nếu yêu cầu
        if nasdaq_only and exchange != "Q":
            skipped_stats["exchange_filtered"] += 1
            continue

        # Lọc: bỏ cổ phiếu tài chính kém (Financial Status = D, E, Q...)
        if exclude_distressed and fin_status not in ("", "N"):
            skipped_stats["distressed"] += 1
            continue

        # Lọc: bỏ symbol có ký tự đặc biệt (warrant, unit, preferred...)
        if any(c in symbol for c in SYMBOL_BLACKLIST_CHARS):
            skipped_stats["bad_symbol"] += 1
            continue

        # Lọc: bỏ symbol quá dài (thường là warrant/unit)
        if len(symbol) > 5:
            skipped_stats["bad_symbol"] += 1
            continue

        # Lọc: bỏ warrant (W), rights (R), units (U) theo suffix
        # Áp dụng khi symbol >= 5 ký tự để tránh lọc nhầm ticker ngắn như "W", "R"
        if len(symbol) >= 5 and symbol.endswith(SYMBOL_WARRANT_SUFFIXES):
            skipped_stats["bad_symbol"] += 1
            continue


        results.append({
            "symbol": symbol,
            "name": name,
            "exchange": exchange,
            "is_etf": is_etf == "Y",
        })

    return results, skipped_stats

# Generate & Save tickers.json
def build_tickers_json(records: list[dict], source_url: str) -> dict:
    """Tạo nội dung tickers.json từ danh sách record đã lọc."""
    tickers = sorted([r["symbol"] for r in records])
    return {
        "_source": source_url,
        "_generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "_total": len(tickers),
        "tickers": tickers,
    }


def save_tickers_json(data: dict, output_path: Path) -> None:
    """Ghi tickers.json ra file local."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"💾 Đã lưu local: {output_path} ({data['_total']} tickers)")


def upload_to_s3(file_path: Path) -> None:
    """Upload tickers.json lên S3."""
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")

    import boto3
    tickers_bucket = os.environ.get(
        "TICKERS_CONFIG_BUCKET",
        "my-nasdaq-stock-processed-2026-430970051812-ap-southeast-1-an",
    )
    tickers_key = os.environ.get("TICKERS_S3_KEY", "config/tickers.json")

    s3 = boto3.client("s3")
    s3.upload_file(str(file_path), tickers_bucket, tickers_key)
    print(f"☁️  Đã upload: s3://{tickers_bucket}/{tickers_key}")

# Main
def main():
    parser = argparse.ArgumentParser(
        description="Tải và lọc danh sách ticker NASDAQ từ nasdaqtrader.com"
    )
    parser.add_argument(
        "--exclude-etf",
        action="store_true",
        help="Loại bỏ ETF khỏi danh sách",
    )
    parser.add_argument(
        "--nasdaq-only",
        action="store_true",
        help="Chỉ lấy chứng khoán niêm yết trên sàn NASDAQ (bỏ NYSE, ARCA...)",
    )
    parser.add_argument(
        "--exclude-distressed",
        action="store_true",
        help="Bỏ cổ phiếu có tình trạng tài chính xấu (Financial Status != N/blank)",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload tickers.json lên S3 sau khi tạo",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chỉ preview kết quả, không lưu file hay upload",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(OUTPUT_FILE),
        help=f"Đường dẫn file output (mặc định: {OUTPUT_FILE})",
    )
    args = parser.parse_args()

    # 1. Fetch
    content = fetch_nasdaq_traded_file()

    # 2. Parse & filter
    records, skipped = parse_tickers(
        content,
        exclude_etf=args.exclude_etf,
        nasdaq_only=args.nasdaq_only,
        exclude_distressed=args.exclude_distressed,
    )

    # 3. Report
    print(f"\n Ket qua loc:")
    print(f"   Ticker hop le (stocks + ETFs):  {len(records):>6,}")
    print(f"   Khong giao dich:                {skipped['not_traded']:>6,}")
    print(f"   Test issue:                     {skipped['test_issue']:>6,}")
    print(f"   ETF bi loai tru (--exclude-etf):{skipped['etf_excluded']:>6,}")
    print(f"   San khac bi loc:                {skipped['exchange_filtered']:>6,}")
    print(f"   Tai chinh xau:                  {skipped['distressed']:>6,}")
    print(f"   Symbol ky tu dac biet:          {skipped['bad_symbol']:>6,}")
    print(f"\n   Vi du 10 ticker dau: {sorted([r['symbol'] for r in records])[:10]}")

    if args.dry_run:
        print("\n[Dry-run mode] Không lưu file hay upload S3.")
        return

    # 4. Build & save
    output_path = Path(args.output)
    data = build_tickers_json(records, NASDAQ_TRADED_URL)
    save_tickers_json(data, output_path)

    # 5. Upload (optional)
    if args.upload:
        upload_to_s3(output_path)

    print("\n✅ Hoàn tất!")
    if not args.upload:
        print("   Dùng --upload để upload lên S3.")


if __name__ == "__main__":
    main()
