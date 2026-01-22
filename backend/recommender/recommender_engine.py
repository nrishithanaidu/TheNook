# recommender_engine.py

import math


class EmotionalRecommender:
    """
    Recommends media based on emotional similarity.
    """

    def __init__(self, emotion_memory):
        self.emotion_memory = emotion_memory

    def emotional_distance(self, e1, e2):
        """
        Euclidean distance between two emotion vectors.
        """
        return math.sqrt((e1[0] - e2[0]) ** 2 + (e1[1] - e2[1]) ** 2)

    def recommend(self, target_emotion: tuple, top_k=5):
        """
        Recommend media closest to desired emotional state.
        """

        recommendations = []

        profiles = self.emotion_memory.all_media_profiles()

        for media_id, emotion in profiles.items():
            if emotion is None:
                continue

            distance = self.emotional_distance(target_emotion, emotion)
            recommendations.append((media_id, distance))

        # smaller distance = better match
        recommendations.sort(key=lambda x: x[1])

        return recommendations[:top_k]
