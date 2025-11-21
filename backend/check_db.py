import sqlite3
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "database.db")

print(f"Checking database at: {DATABASE_PATH}")

try:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables: {tables}")
    
    # Check records count
    cursor.execute("SELECT count(*) FROM records")
    count = cursor.fetchone()[0]
    print(f"Total records: {count}")
    
    # Check actual records
    cursor.execute("SELECT id, task_id, created_at FROM records ORDER BY created_at DESC LIMIT 5")
    rows = cursor.fetchall()
    print("Recent records:")
    for row in rows:
        print(row)
        
    conn.close()
except Exception as e:
    print(f"Error reading database: {e}")
