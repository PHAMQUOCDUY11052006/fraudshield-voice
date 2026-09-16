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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            timestamp TEXT,
            filename TEXT,
            score REAL,
            threat TEXT,
            call_source TEXT,
            suspect_type TEXT,
            audio_path TEXT
        )
    ''')
    cursor.execute("PRAGMA table_info(scan_logs)")
    cols = [c[1] for c in cursor.fetchall()]
    if "username" not in cols:
        cursor.execute("ALTER TABLE scan_logs ADD COLUMN username TEXT DEFAULT 'Guest'")
    if "audio_path" not in cols:
        cursor.execute("ALTER TABLE scan_logs ADD COLUMN audio_path TEXT DEFAULT ''")
        
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

def save_scan_result(username, filename, score, threat, call_source, suspect_type, audio_path=""):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO scan_logs (username, timestamp, filename, score, threat, call_source, suspect_type, audio_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (username, now_str, filename, score, threat, call_source, suspect_type, audio_path))
    conn.commit()
    conn.close()

def get_user_scans(username, limit=10):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, timestamp, filename, score, threat, call_source, suspect_type, audio_path
        FROM scan_logs
        WHERE username = ?
        ORDER BY id DESC
        LIMIT ?
    ''', (username, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users')
    rows = [r[0] for r in cursor.fetchall()]
    conn.close()
    return rows

def get_all_scans_admin(limit=100):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, username, timestamp, filename, score, threat, call_source, suspect_type, audio_path
        FROM scan_logs
        ORDER BY id DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

init_db()
