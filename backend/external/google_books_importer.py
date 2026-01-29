import requests
import sqlite3
from pathlib import Path
from recommender.emotion_parser import parse_emotion

DB_PATH = Path(__file__).parents[1] / "database" / "nook.db"

BASE_URL = "https://www.googleapis.com/books/v1/volumes"


def fetch_books(query, max_results=40, start_index=0):
    params = {
        "q": query,
        "maxResults": max_results,
        "startIndex": start_index
    }
    response = requests.get(BASE_URL, params=params, timeout=10)
    return response.json().get("items", [])


def import_books():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    queries = [
    "romance novel",
    "dark romance",
    "psychological thriller book",
    "fantasy fiction",
    "young adult fiction",
    "classic literature",
    "mystery novel",
    "historical fiction",
    "self discovery book",
    "coming of age novel",
    "emotional fiction",
    "modern literature"
]


    total = 0

    for query in queries:
        for start in range(0, 400, 40):   
            books = fetch_books(query, start_index=start)

            for book in books:
                info = book.get("volumeInfo", {})
                title = info.get("title")
                description = info.get("description", "")

                if not title or not description:
                    continue

                emotion = parse_emotion(description)

                cursor.execute("""
                    INSERT OR IGNORE INTO media
                    (id, title, media_type, emotion_x, emotion_y)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    f"book_{book.get('id')}",
                    title,
                    "book",
                    emotion[0],
                    emotion[1]
                ))

                total += 1

    conn.commit()
    conn.close()

    print(f"✅ Imported ~{total} books")


if __name__ == "__main__":
    import_books()
