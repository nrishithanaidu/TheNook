import sqlite3
import sys
from pathlib import Path

# force backend folder into import path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

DB_PATH = Path(__file__).parent / "nook.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS media (
        id TEXT PRIMARY KEY,
        title TEXT,
        media_type TEXT,
        emotion_x REAL,
        emotion_y REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS emotion_logs (
        user_id TEXT,
        media_id TEXT,
        emotion_x REAL,
        emotion_y REAL
    )
    """)

    conn.commit()
    conn.close()
