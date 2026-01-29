import csv
import sqlite3
from pathlib import Path

# Path to your database
DB_PATH = Path(__file__).parents[1] / "database" / "nook.db"

# Path to Spotify dataset
CSV_PATH = Path(__file__).parent / "data.csv"


def normalize(value):
    """
    Convert 0–1 → -1 to +1
    """
    return round(value * 2 - 1, 3)


def import_spotify_songs(limit=1000):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    inserted = 0

    with open(CSV_PATH, encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            if inserted >= limit:
                break

            try:
                title = row["name"]
                artist = row["artists"]

                valence = float(row["valence"])
                energy = float(row["energy"])

                emotion_x = normalize(valence)
                emotion_y = normalize(energy)

                media_id = f"spotify_{inserted}"

                cursor.execute("""
                    INSERT OR IGNORE INTO media
                    (id, title, media_type, emotion_x, emotion_y)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    media_id,
                    f"{title} — {artist}",
                    "music",
                    emotion_x,
                    emotion_y
                ))

                inserted += 1

            except Exception:
                continue

    conn.commit()
    conn.close()

    print(f"🎵 Imported {inserted} Spotify songs")


if __name__ == "__main__":
    import_spotify_songs(limit=1500)
