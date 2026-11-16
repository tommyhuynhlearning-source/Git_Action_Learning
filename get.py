"""
Lấy giá mới nhất của cổ phiếu Mỹ (Finnhub /quote) rồi insert vào mydb.stock_quotes.

Cách chạy:
    python fetch_stock_quotes.py                 # dùng danh sách mặc định
    python fetch_stock_quotes.py -s AAPL MSFT    # chọn symbol
    python fetch_stock_quotes.py --dry-run       # chỉ in ra, không ghi DB

.env cần có:
    db_password=...
    finnhub_api_key=...
"""
import argparse
import os
import sys
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import mysql.connector
import requests
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = dict(
    host="finance-data.clwue00u2hp5.ap-southeast-1.rds.amazonaws.com",
    port=3306,
    database="mydb",
    user="admin",
    password=os.getenv("db_password"),
    ssl_ca="./global-bundle.pem",
    ssl_disabled=False,
)

API_KEY = os.getenv("finnhub_api_key")
QUOTE_URL = "https://finnhub.io/api/v1/quote"
DEFAULT_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META"]
NY_TZ = ZoneInfo("America/New_York")

INSERT_SQL = """
    INSERT INTO stock_quotes
        (symbol, current_price, change_amount, percent_change,
         high_price, low_price, open_price, prev_close,
         quote_time, quote_date, fetched_at)
    VALUES
        (%(symbol)s, %(current_price)s, %(change_amount)s, %(percent_change)s,
         %(high_price)s, %(low_price)s, %(open_price)s, %(prev_close)s,
         %(quote_time)s, %(quote_date)s, %(fetched_at)s)
    ON DUPLICATE KEY UPDATE fetched_at = VALUES(fetched_at)
"""


def fetch_quote(symbol):
    """Gọi Finnhub, trả về dict khớp với các cột của bảng (hoặc None nếu lỗi)."""
    try:
        resp = requests.get(
            QUOTE_URL, params={"symbol": symbol, "token": API_KEY}, timeout=10
        )
        resp.raise_for_status()
        d = resp.json()
    except requests.RequestException as e:
        print(f"[{symbol}] lỗi gọi API: {e}")
        return None

    # Symbol không tồn tại -> Finnhub trả về toàn số 0, t = 0
    if not d.get("t") or d.get("c") in (None, 0):
        print(f"[{symbol}] không có dữ liệu (sai symbol?)")
        return None

    quote_dt_utc = datetime.fromtimestamp(d["t"], tz=timezone.utc)
    return {
        "symbol": symbol,
        "current_price": d["c"],
        "change_amount": d["d"],
        "percent_change": d["dp"],
        "high_price": d["h"],
        "low_price": d["l"],
        "open_price": d["o"],
        "prev_close": d["pc"],
        # quote_time lưu UTC; quote_date là ngày giao dịch theo giờ New York
        "quote_time": quote_dt_utc.replace(tzinfo=None),
        "quote_date": quote_dt_utc.astimezone(NY_TZ).date(),
        "fetched_at": datetime.now(timezone.utc).replace(tzinfo=None),
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch US stock quotes -> MySQL")
    parser.add_argument("-s", "--symbol", nargs="+", help="e.g. -s AAPL MSFT")
    parser.add_argument("--dry-run", action="store_true", help="không ghi vào DB")
    args = parser.parse_args()

    if not API_KEY:
        sys.exit("Thiếu finnhub_api_key trong .env")

    symbols = [s.upper() for s in (args.symbol or DEFAULT_SYMBOLS)]

    rows = []
    for sym in symbols:
        row = fetch_quote(sym)
        if row:
            rows.append(row)
            print(
                f"[{sym}] {row['current_price']} "
                f"({row['percent_change']:+.2f}%)  quote_time={row['quote_time']} UTC  "
                f"quote_date={row['quote_date']}"
            )
        time.sleep(0.2)  # tránh vượt rate limit (free: 60 call/phút)

    if not rows:
        sys.exit("Không lấy được dữ liệu nào.")

    if args.dry_run:
        print(f"\nDry-run: bỏ qua insert {len(rows)} dòng.")
        return

    conn = mysql.connector.connect(**DB_CONFIG)
    try:
        cur = conn.cursor()
        cur.executemany(INSERT_SQL, rows)
        conn.commit()
        cur.close()
        print(f"\nĐã ghi {len(rows)} dòng vào stock_quotes.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
