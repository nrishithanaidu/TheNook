from recommender.emotion_parser import parse_emotion
from recommender.vector_utils import average_vectors
from recommender.emotion_memory import (
    store_user_emotion,
    get_user_emotions
)
from recommender.recommender_engine import EmotionalRecommender


def log_user_emotion(user_id, media_id, emotion_text):
    emotion_vector = parse_emotion(emotion_text)

    store_user_emotion(
        user_id=user_id,
        media_id=media_id,
        emotion_vector=emotion_vector
    )


def get_user_recommendations(user_id, desired_mood=None):
    user_emotions = get_user_emotions(user_id)

    if not user_emotions:
        return []

    # target emotion
    if desired_mood:
        target_emotion = parse_emotion(desired_mood)
    else:
        target_emotion = average_vectors(user_emotions)

    recommender = EmotionalRecommender()

    return recommender.recommend(
        target_emotion=target_emotion,
        top_k=5
    )
