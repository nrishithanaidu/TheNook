import os
import requests
import sqlite3

from recommender.emotion_parser import parse_emotion
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

if not TMDB_API_KEY:
    raise ValueError("TMDB_API_KEY not found in environment")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "database", "nook.db")


def get_movies_from_tmdb(pages=1):
    movies = []

    for page in range(1, pages + 1):
        try:
            url = "https://api.themoviedb.org/3/trending/movie/week"

            response = requests.get(
                url,
                params={
                    "api_key": TMDB_API_KEY,
                    "page": page
                },
                timeout=10
            )

            data = response.json()

            for movie in data.get("results", []):
                movies.append({
                    "id": f"tmdb_{movie['id']}",
                    "title": movie["title"],
                    "overview": movie.get("overview", "")
                })

        except Exception as e:
            print(f"⚠️ Skipping page {page}: {e}")
            continue

    return movies


def store_movies(movies):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for movie in movies:
        if not movie["overview"]:
            continue

        emotion_vector = parse_emotion(movie["overview"])

        cursor.execute("""
            INSERT OR IGNORE INTO media
            (id, title, media_type, emotion_x, emotion_y)
            VALUES (?, ?, ?, ?, ?)
        """, (
            movie["id"],
            movie["title"],
            "movie",
            emotion_vector[0],
            emotion_vector[1]
        ))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    print("🎬 Fetching movies from TMDB...")
    movies = get_movies_from_tmdb(pages=3)
    print(f"Found {len(movies)} movies")
    store_movies(movies)
    print("✅ TMDB movies imported into database")
