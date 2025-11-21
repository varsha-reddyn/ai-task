import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "database.db")

print(f"Database path: {DATABASE_PATH}")

def init_db():
    """Initialize the database and create tables if they don't exist."""
    try:
        print(f"Initializing database at {DATABASE_PATH}...")
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                raw_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        # Create a new database file if it fails
        try:
            if os.path.exists(DATABASE_PATH):
                print("Attempting to recreate database file...")
                # Don't delete, just try to open/create
            
            conn = sqlite3.connect(DATABASE_PATH)
            conn.close()
        except Exception as e2:
            print(f"Fatal error creating database: {e2}")

def insert_record(task_id: str, raw_json: Dict[str, Any]) -> int:
    """Insert a new record into the database."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO records (task_id, raw_json) VALUES (?, ?)",
        (task_id, json.dumps(raw_json))
    )
    
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return record_id

def get_all_records() -> List[Dict[str, Any]]:
    """Retrieve all records from the database."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM records ORDER BY created_at DESC")
    rows = cursor.fetchall()
    
    conn.close()
    
    records = []
    for row in rows:
        record = dict(row)
        record['raw_json'] = json.loads(record['raw_json'])
        records.append(record)
    
    return records

def get_record_by_id(record_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single record by ID."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM records WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    
    conn.close()
    
    if row:
        record = dict(row)
        record['raw_json'] = json.loads(record['raw_json'])
        return record
    return None

def get_record_by_task_id(task_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single record by task ID."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM records WHERE task_id = ?", (task_id,))
    row = cursor.fetchone()
    
    conn.close()
    
    if row:
        record = dict(row)
        record['raw_json'] = json.loads(record['raw_json'])
        return record
    return None

def update_record(record_id: int, raw_json: Dict[str, Any]) -> bool:
    """Update an existing record."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE records SET raw_json = ?, updated_at = ? WHERE id = ?",
        (json.dumps(raw_json), datetime.now().isoformat(), record_id)
    )
    
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    return rows_affected > 0

def delete_record(record_id: int) -> bool:
    """Delete a record by ID."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM records WHERE id = ?", (record_id,))
    
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    return rows_affected > 0
