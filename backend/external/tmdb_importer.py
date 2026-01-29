import os
import requests
import sqlite3
from pathlib import Path

from recommender.emotion_parser import parse_emotion



TMDB_API_KEY = os.getenv("TMDB_API_KEY")

if not TMDB_API_KEY:
    raise ValueError("TMDB_API_KEY not found in environment")

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "database" / "nook.db"

BASE_URL = "https://api.themoviedb.org/3"

# Movie categories
ENDPOINTS = [
    "trending/movie/week",
    "movie/popular",
    "movie/top_rated",
    "movie/now_playing",
    "movie/upcoming",
    "discover/movie?with_genres=18",
    "discover/movie?with_genres=10749",
    "discover/movie?with_genres=53",
    "discover/movie?with_genres=16",
    "discover/movie?with_genres=27",
    "discover/movie?with_genres=35",
    "discover/movie?with_genres=80",
    "discover/movie?with_original_language=ko",
    "discover/movie?with_original_language=ja",
    "discover/movie?with_original_language=fr",
    "discover/movie?with_original_language=es",
    "discover/movie?with_original_language=hi"
]

# --------------------
# FETCH MOVIES
# --------------------

def fetch_movies():
    movies = []

    for endpoint in ENDPOINTS:
        print(f"🎬 Fetching: {endpoint}")

        for page in range(1, 6):  # 5 pages each
            try:
                url = f"{BASE_URL}/{endpoint}"

                response = requests.get(
                    url,
                    params={
                        "api_key": TMDB_API_KEY,
                        "page": page,
                        "language": "en-US"
                    },
                    timeout=10
                )

                data = response.json()

                for m in data.get("results", []):
                    overview = m.get("overview", "")

                    if not overview:
                        continue

                    movies.append({
                        "id": f"tmdb_{m['id']}",
                        "title": m.get("title"),
                        "overview": overview
                    })

            except Exception as e:
                print(f"⚠️ Skipping page {page}: {e}")

    return movies


# --------------------
# STORE MOVIES
# --------------------

def store_movies(movies):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    added = 0

    for movie in movies:
        try:
            emotion_x, emotion_y = parse_emotion(movie["overview"])
                # soften intensity
            emotion_y *= 0.6

                # clamp range
            emotion_y = max(-1.0, min(1.0, emotion_y))


            cursor.execute("""
                INSERT OR IGNORE INTO media
                (id, title, media_type, emotion_x, emotion_y)
                VALUES (?, ?, ?, ?, ?)
            """, (
                movie["id"],
                movie["title"],
                "movie",
                emotion_x,
                emotion_y
            ))

            added += 1

        except Exception:
            continue

    conn.commit()
    conn.close()

    print(f"✅ Imported approx {added} movies")


# --------------------
# MAIN
# --------------------

if __name__ == "__main__":
    print("🚀 Starting TMDB bulk import...")
    movies = fetch_movies()
    print(f"📦 Total fetched: {len(movies)}")
    store_movies(movies)
    print("🎉 TMDB import completed")
