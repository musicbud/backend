import sqlite3
import os
import time

path = '/home/ubuntu/musicbud/db.sqlite3'   


def test_db_connection():
    print(f"Testing connection to {path}")
    print(f"Database file exists: {os.path.exists(path)}")
    print(f"Database file is readable: {os.access(path, os.R_OK)}")
    print(f"Database file is writable: {os.access(path, os.W_OK)}")

    start_time = time.time()
    try:
        conn = sqlite3.connect(path, timeout=10)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        end_time = time.time()
        print(f"Connection successful. Result: {result}")
        print(f"Connection test completed in {end_time - start_time:.2f} seconds")
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")

if __name__ == "__main__":
    test_db_connection()
