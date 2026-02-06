import math
import random
from typing import List, Tuple, Optional

from recommender import db_connector


class EmotionalRecommender:

    MOOD_MAP = {
        "happy": (0.8, 0.8),
        "excited": (0.9, 0.9),
        "energetic": (0.7, 0.9),
        "thrilled": (0.9, 0.95),

        "calm": (0.1, 0.2),
        "peaceful": (0.2, 0.2),
        "relaxed": (0.3, 0.2),
        "content": (0.5, 0.3),
        "serene": (0.3, 0.15),

        "anxious": (-0.6, 0.8),
        "tense": (-0.5, 0.7),
        "intense": (-0.4, 0.9),
        "overwhelming": (-0.6, 0.9),
        "stressed": (-0.7, 0.85),

        "sad": (-0.6, 0.3),
        "lonely": (-0.6, 0.3),
        "melancholic": (-0.5, 0.4),
        "empty": (-0.7, 0.2),
        "numb": (-0.4, 0.1),

        "neutral": (0.0, 0.5),
        "indifferent": (0.0, 0.3),
    }

    def emotional_distance(self, e1, e2):
        return math.sqrt((e1[0] - e2[0]) ** 2 + (e1[1] - e2[1]) ** 2)

    def mood_to_emotion(self, mood):
        mood_lower = mood.lower().strip()
        return self.MOOD_MAP.get(mood_lower, (0.0, 0.5))

    def moods_to_emotion(self, moods):
        if not moods:
            return (0.0, 0.5)

        emotions = [self.mood_to_emotion(m) for m in moods]
        avg_x = sum(e[0] for e in emotions) / len(emotions)
        avg_y = sum(e[1] for e in emotions) / len(emotions)

        return (round(avg_x, 3), round(avg_y, 3))

    def recommend(
        self,
        target_emotion: Tuple[float, float],
        user_id: Optional[str] = None,
        media_type: Optional[str] = None,
        top_k: int = 5,
    ) -> List[dict]:

        media_items = db_connector.get_media_with_emotions()
        if not media_items:
            return []

        ranked = []

        for media_id, title, m_type, moods, rating in media_items:

            if media_type and m_type != media_type:
                continue

            if not moods:
                continue

            media_emotion = self.moods_to_emotion(moods)
            distance = self.emotional_distance(target_emotion, media_emotion)

            ranked.append({
                "id": media_id,
                "title": title,
                "type": m_type,
                "distance": round(distance, 3),
                "emotion": media_emotion,
                "moods": moods,
                "rating": rating,
                "match_percentage": round((1 - min(distance, 2) / 2) * 100, 1),
            })

        # ✅ Shuffle first to avoid same repeated ties
        random.shuffle(ranked)

        # ✅ Sort by best match
        ranked.sort(key=lambda x: x["distance"])

        # ✅ Diversity filter: max 3 per media type
        final = []
        type_count = {}

        for item in ranked:
            t = item["type"]
            type_count[t] = type_count.get(t, 0)

            if type_count[t] < 3:
                final.append(item)
                type_count[t] += 1

            if len(final) == top_k:
                break

        return final

    def recommend_opposite(
        self,
        current_emotion: Tuple[float, float],
        media_type: Optional[str] = None,
        top_k: int = 5,
    ) -> List[dict]:

        opposite_emotion = (-current_emotion[0], 1 - current_emotion[1])

        return self.recommend(
            target_emotion=opposite_emotion,
            media_type=media_type,
            top_k=top_k,
        )
