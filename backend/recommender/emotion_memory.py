# emotion_memory.py

from collections import defaultdict


class EmotionMemory:
    """
    Stores emotional outcomes of media consumption.
    Learns average emotional impact per media item.
    """

    def __init__(self):
        # media_id -> list of (valence, arousal)
        self.memory = defaultdict(list)

    def log_emotion(self, media_id: str, emotion_vector: tuple):
        """
        Store emotional response after consuming media.
        """
        self.memory[media_id].append(emotion_vector)

    def get_average_emotion(self, media_id: str):
        """
        Returns average (valence, arousal) for a media item.
        """
        emotions = self.memory.get(media_id)

        if not emotions:
            return None

        avg_valence = sum(v for v, a in emotions) / len(emotions)
        avg_arousal = sum(a for v, a in emotions) / len(emotions)

        return round(avg_valence, 3), round(avg_arousal, 3)

    def all_media_profiles(self):
        """
        Returns emotional profile for all media.
        """
        profiles = {}

        for media_id in self.memory:
            profiles[media_id] = self.get_average_emotion(media_id)

        return profiles
