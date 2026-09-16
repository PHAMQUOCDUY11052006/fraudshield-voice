import sqlite3
from datetime import datetime

DB_NAME = "audit_log.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            filename TEXT,
            score REAL,
            threat TEXT,
            call_source TEXT,
            suspect_type TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_scan_result(filename, score, threat, call_source, suspect_type):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO scan_logs (timestamp, filename, score, threat, call_source, suspect_type)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (now_str, filename, score, threat, call_source, suspect_type))
    conn.commit()
    conn.close()

def get_recent_scans(limit=5):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, filename, score, threat, call_source, suspect_type
        FROM scan_logs
        ORDER BY id DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows
