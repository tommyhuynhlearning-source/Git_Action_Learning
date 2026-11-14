import mysql.connector
import boto3
import os
from dotenv import load_dotenv

load_dotenv()
password = os.getenv('db_password')

conn = None
try:
    conn = mysql.connector.connect(
        host='finace-data.clwue00u2hp5.ap-southeast-1.rds.amazonaws.com',
        port=3306,
        database='mydb',
        user='admin',
        password=password,
        ssl_disabled=False,
        autocommit=True,
    ssl_ca='./global-bundle.pem'
    )
    cur = conn.cursor()
    cur.execute('SELECT VERSION();')
    print(cur.fetchone()[0])
    cur.close()
except Exception as e:
    print(f"Database error: {e}")
    raise
finally:
    if conn:
        conn.close()