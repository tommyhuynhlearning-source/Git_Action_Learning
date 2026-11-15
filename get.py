import argparse
import csv
import os

import mysql.connector
from dotenv import load_dotenv

load_dotenv()
password = os.getenv("db_password")

DB_CONFIG = dict(
    host="finance-data.clwue00u2hp5.ap-southeast-1.rds.amazonaws.com",
    port=3306,
    database="mydb",
    user="admin",
    password=password,
    ssl_ca="./global-bundle.pem",
    ssl_disabled=False,
)

COLUMNS = (
    "id, symbol, current_price, change_amount, percent_change, "
    "high_price, low_price, open_price, prev_close, quote_time, fetched_at"
)


def build_query(symbols, latest, limit):
    """Return (sql, params) based on the CLI options."""
    where = ""
    params = []
    if symbols:
        placeholders = ", ".join(["%s"] * len(symbols))
        where = f"WHERE symbol IN ({placeholders})"
        params.extend(symbols)

    if latest:
        # Most recent quote for each symbol
        sql = f"""
            SELECT {COLUMNS}
            FROM stock_quotes q
            JOIN (
                SELECT symbol AS s, MAX(quote_time) AS max_time
                FROM stock_quotes
                {where}
                GROUP BY symbol
            ) m ON q.symbol = m.s AND q.quote_time = m.max_time
            ORDER BY q.symbol
        """
    else:
        sql = f"""
            SELECT {COLUMNS}
            FROM stock_quotes
            {where}
            ORDER BY quote_time DESC, symbol
            LIMIT %s
        """
        params.append(limit)

    return sql, params


def print_table(rows):
    if not rows:
        print("No data found.")
        return

    headers = list(rows[0].keys())
    widths = {h: max(len(h), *(len(str(r[h])) for r in rows)) for h in headers}

    line = " | ".join(h.ljust(widths[h]) for h in headers)
    print(line)
    print("-+-".join("-" * widths[h] for h in headers))
    for r in rows:
        print(" | ".join(str(r[h]).ljust(widths[h]) for h in headers))
    print(f"\n{len(rows)} row(s)")


def save_csv(rows, path):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved to {path}")


def main():
    parser = argparse.ArgumentParser(description="Read data from stock_quotes")
    parser.add_argument("-s", "--symbol", nargs="+", help="e.g. -s AAPL MSFT")
    parser.add_argument("-n", "--limit", type=int, default=20,
                        help="max rows (default 20, ignored with --latest)")
    parser.add_argument("--latest", action="store_true",
                        help="only the latest quote per symbol")
    parser.add_argument("--csv", metavar="FILE", help="also export to a CSV file")
    args = parser.parse_args()

    symbols = [s.upper() for s in args.symbol] if args.symbol else None
    sql, params = build_query(symbols, args.latest, args.limit)

    conn = mysql.connector.connect(**DB_CONFIG)
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()

    print_table(rows)
    if args.csv:
        save_csv(rows, args.csv)


if __name__ == "__main__":
    main()