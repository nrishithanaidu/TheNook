# emotion_memory.py

from collections import defaultdict

# -------------------------------------------------
# In-memory emotional storage (safe + simple)
# -------------------------------------------------

# user_id -> list of emotion vectors
_user_emotion_memory = defaultdict(list)


def store_user_emotion(user_id: str, media_id: str, emotion_vector: tuple):
    """
    Store a user's emotional response.
    media_id is kept for future extension (analytics, clustering).
    """
    _user_emotion_memory[user_id].append(emotion_vector)


def get_user_emotions(user_id: str):
    """
    Return all emotion vectors for a user.
    """
    return _user_emotion_memory.get(user_id, [])


# -------------------------------------------------
# Optional ML profile class (kept for architecture)
# -------------------------------------------------

class EmotionMemory:
    """
    Media-centric emotion memory (used internally by recommender).
    """

    def __init__(self):
        self.memory = defaultdict(list)

    def log_emotion(self, media_id: str, emotion_vector: tuple):
        self.memory[media_id].append(emotion_vector)

    def get_average_emotion(self, media_id: str):
        emotions = self.memory.get(media_id)
        if not emotions:
            return None

        avg_valence = sum(v for v, a in emotions) / len(emotions)
        avg_arousal = sum(a for v, a in emotions) / len(emotions)

        return round(avg_valence, 3), round(avg_arousal, 3)

    def all_media_profiles(self):
        return {
            media_id: self.get_average_emotion(media_id)
            for media_id in self.memory
        }
