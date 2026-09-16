import sqlite3
import hashlib
from datetime import datetime

DB_NAME = "audit_log.db"

def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hash(password, hashed_text):
    return make_hash(password) == hashed_text

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Bang users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    
    # 2. Tao bang scan_logs neu chua co
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            timestamp TEXT,
            filename TEXT,
            score REAL,
            threat TEXT,
            call_source TEXT,
            suspect_type TEXT
        )
    ''')
    
    # 3. Kiem tra va tu dong them cot username neu bang cu chua co
    cursor.execute("PRAGMA table_info(scan_logs)")
    columns = [col[1] for col in cursor.fetchall()]
    if "username" not in columns:
        cursor.execute("ALTER TABLE scan_logs ADD COLUMN username TEXT DEFAULT 'Guest'")
        
    conn.commit()
    conn.close()

def add_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, make_hash(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
    data = cursor.fetchone()
    conn.close()
    if data and check_hash(password, data[0]):
        return True
    return False

def save_scan_result(username, filename, score, threat, call_source, suspect_type):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO scan_logs (username, timestamp, filename, score, threat, call_source, suspect_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (username, now_str, filename, score, threat, call_source, suspect_type))
    conn.commit()
    conn.close()

def get_user_scans(username, limit=10):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, filename, score, threat, call_source, suspect_type
        FROM scan_logs
        WHERE username = ?
        ORDER BY id DESC
        LIMIT ?
    ''', (username, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows

init_db()
