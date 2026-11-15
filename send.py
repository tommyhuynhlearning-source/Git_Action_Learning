import mysql.connector
import boto3
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
import finnhub

load_dotenv()
password = os.getenv("db_password")
finhub_api_key = os.getenv("finhub_api_key")
conn = None

SYMBOLS = ["AAPL", "MSFT", "GOOGL"]

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS stock_quotes (
    id             BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol         VARCHAR(10)   NOT NULL,
    current_price  DECIMAL(12,4),
    change_amount  DECIMAL(12,4),
    percent_change DECIMAL(10,4),
    high_price     DECIMAL(12,4),
    low_price      DECIMAL(12,4),
    open_price     DECIMAL(12,4),
    prev_close     DECIMAL(12,4),
    quote_time     DATETIME      NOT NULL,
    fetched_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_symbol_time (symbol, quote_time)
)
"""

INSERT_SQL = """
INSERT INTO stock_quotes
    (symbol, current_price, change_amount, percent_change,
     high_price, low_price, open_price, prev_close, quote_time)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    current_price = VALUES(current_price),
    change_amount = VALUES(change_amount),
    percent_change = VALUES(percent_change)
"""

def main():
    client = finnhub.Client(api_key=finhub_api_key)

    conn = mysql.connector.connect(
        host="finance-data.clwue00u2hp5.ap-southeast-1.rds.amazonaws.com",
        port=3306,
        database="mydb",
        user="admin",
        password=password,
        ssl_ca="./global-bundle.pem",
        ssl_disabled=False,
        autocommit=True,
    )
    try:
        cur = conn.cursor()
        cur.execute(CREATE_TABLE)

        rows = []
        for symbol in SYMBOLS:
            q = client.quote(symbol)
            if not q.get("t"):  # symbol sai hoặc không có data
                print(f"Bỏ qua {symbol}: không có data")
                continue
            quote_time = datetime.fromtimestamp(q["t"], tz=timezone.utc).replace(tzinfo=None)
            rows.append((symbol, q["c"], q["d"], q["dp"],
                         q["h"], q["l"], q["o"], q["pc"], quote_time))

        cur.executemany(INSERT_SQL, rows)
        print(f"Đã insert/update {cur.rowcount} dòng")

        cur.execute("SELECT symbol, current_price, quote_time FROM stock_quotes ORDER BY id DESC LIMIT 5")
        for r in cur.fetchall():
            print(r)
        cur.close()
    finally:
        conn.close()

if __name__ == "__main__":
    main()