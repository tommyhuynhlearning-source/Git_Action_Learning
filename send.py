import os
import smtplib
from email.message import EmailMessage

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_HOST = "finance-data.clwue00u2hp5.ap-southeast-1.rds.amazonaws.com"
DB_NAME = "mydb"
DB_USER = "admin"


# ---------------------------------------------------------------- DATABASE
def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        port=3306,
        database=DB_NAME,
        user=DB_USER,
        password=os.getenv("db_password"),
        ssl_ca="./global-bundle.pem",
        ssl_disabled=False,
        autocommit=True,
    )


def list_tables():
    """Liệt kê tất cả table đang có trong DB."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SHOW TABLES")
        tables = [row[0] for row in cur.fetchall()]
        cur.close()
    finally:
        conn.close()

    print("\n=== Các table trong DB ===")
    if not tables:
        print("DB chưa có table nào")
    for t in tables:
        print("-", t)
    return tables


def view_table(table_name, limit=10):
    """Xem cấu trúc cột, tổng số dòng và vài dòng dữ liệu của một table."""
    conn = get_connection()
    try:
        cur = conn.cursor()

        # Tên table không thể truyền bằng %s, nên kiểm tra với danh sách thật
        # để tránh SQL injection
        cur.execute("SHOW TABLES")
        valid_tables = [row[0] for row in cur.fetchall()]
        if table_name not in valid_tables:
            print(f"Table '{table_name}' không tồn tại. Hiện có: {valid_tables}")
            return

        # Cấu trúc các cột
        cur.execute(f"DESCRIBE `{table_name}`")
        print(f"\n=== Cấu trúc table {table_name} ===")
        for col in cur.fetchall():
            print(col)  # (tên cột, kiểu dữ liệu, null?, key, default, extra)

        # Số dòng
        cur.execute(f"SELECT COUNT(*) FROM `{table_name}`")
        print(f"\nTổng số dòng: {cur.fetchone()[0]}")

        # Dữ liệu
        cur.execute(f"SELECT * FROM `{table_name}` LIMIT %s", (limit,))
        col_names = [d[0] for d in cur.description]
        print(f"\n=== {limit} dòng đầu của {table_name} ===")
        print(col_names)
        for row in cur.fetchall():
            print(row)
        cur.close()
    finally:
        conn.close()


# ------------------------------------------------------------------- EMAIL
def send_email(subject="US Stock Today", body="US STOCK MARKET TODAY"):
    gmail_user = os.getenv("gmail_user")
    gmail_app_password = os.getenv("gmail_password")
    recipient_email = os.getenv("recipient_email")

    if not (gmail_user and gmail_app_password and recipient_email):
        print("Thiếu gmail_user, gmail_password hoặc recipient_email trong .env")
        return

    msg = EmailMessage()
    msg["From"] = gmail_user
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, gmail_app_password)
        server.send_message(msg)

    print("Sent email successfully!")


# -------------------------------------------------------------------- MAIN
def main():
    tables = list_tables()  # xem DB có những table nào

    # Xem chi tiết một table cụ thể:
    # view_table("stock_quotes")

    # Hoặc xem hết tất cả các table:
    for t in tables:
        view_table(t)

    send_email()


if __name__ == "__main__":
    main()
