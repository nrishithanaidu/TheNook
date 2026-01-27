import math
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parents[1] / "database" / "nook.db"


class EmotionalRecommender:
    """
    Emotion-based recommender using stored media emotion vectors.
    """

    def emotional_distance(self, e1, e2):
        return math.sqrt(
            (e1[0] - e2[0]) ** 2 +
            (e1[1] - e2[1]) ** 2
        )

    def recommend(self, target_emotion: tuple, top_k=5):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, title, media_type, emotion_x, emotion_y
            FROM media
            WHERE emotion_x IS NOT NULL
            AND emotion_y IS NOT NULL
        """)

        rows = cursor.fetchall()
        conn.close()

        ranked = []

        for media_id, title, media_type, ex, ey in rows:
            distance = self.emotional_distance(
                target_emotion,
                (ex, ey)
            )

            ranked.append({
                "id": media_id,
                "title": title,
                "type": media_type,
                "distance": round(distance, 3)
            })

        ranked.sort(key=lambda x: x["distance"])

        return ranked[:top_k]
