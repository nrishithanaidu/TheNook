import sys
from pathlib import Path

# absolute path to backend/database
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from db import init_db, get_connection


def seed_media():
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    media_items = [
        ("pied_piper_song", "Pied Piper", "music", -0.45, 0.90),
        ("dark_romance_book", "Dark Romance Novel", "book", -0.55, 0.45),
        ("thriller_movie", "Psychological Thriller", "movie", -0.60, 0.85),
        ("soft_piano_music", "Soft Piano", "music", 0.20, 0.20),
    ]

    for item in media_items:
        cursor.execute("""
            INSERT OR IGNORE INTO media
            (id, title, media_type, emotion_x, emotion_y)
            VALUES (?, ?, ?, ?, ?)
        """, item)

    conn.commit()
    conn.close()

    print("✅ Database seeded with initial media.")


if __name__ == "__main__":
    seed_media()
