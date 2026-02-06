from typing import Optional, Tuple
from recommender.emotion_parser import parse_emotion
from recommender.vector_utils import average_vectors
from recommender.emotion_memory import store_user_emotion, get_user_emotions
from recommender.recommender_engine import EmotionalRecommender
from recommender.db_connector import (
    save_user_emotion_to_db,
    get_user_emotions_from_db,
    get_average_user_emotion
)


def log_user_emotion(user_id: str, media_id: str, media_type: str, 
                    emotion_text: str) -> Tuple[float, float]:
    """
    Log a user's emotional response to media.
    
    Stores both in memory (for fast access during session) and 
    in database (for persistence across sessions).
    
    Args:
        user_id: User's unique ID
        media_id: ID of media item
        media_type: Type of media ('movie', 'book', 'podcast', 'album')
        emotion_text: Free-text emotional description
        
    Returns:
        Tuple (valence, arousal) of parsed emotion
    """
    emotion_vector = parse_emotion(emotion_text)
    
    store_user_emotion(
        user_id=user_id,
        media_id=media_id,
        emotion_vector=emotion_vector
    )
    
    save_user_emotion_to_db(
        user_id=user_id,
        media_id=media_id,
        media_type=media_type,
        emotion_x=emotion_vector[0],
        emotion_y=emotion_vector[1],
        emotion_text=emotion_text
    )
    
    return emotion_vector


def get_user_recommendations(user_id: str, 
                            desired_mood: Optional[str] = None, 
                            media_type: Optional[str] = None, 
                            limit: int = 5,
                            mode: str = "similar"):
    """
    Get personalized recommendations for a user.
    
    Args:
        user_id: User's unique ID
        desired_mood: Optional mood text (e.g., "happy", "calm", "intense")
        media_type: Optional filter ('movie', 'book', 'podcast', 'album')
        limit: Number of recommendations to return
        mode: "similar" for matching emotions, "opposite" for mood change
        
    Returns:
        List of recommended media items with emotion distances
    """
    # First try to get emotions from memory (fast)
    user_emotions = get_user_emotions(user_id)
    
    # If not in memory, get from database (first session)
    if not user_emotions:
        db_emotions = get_user_emotions_from_db(user_id)
        user_emotions = [(e[3], e[4]) for e in db_emotions if e[3] is not None]
    
    # Determine target emotion
    if desired_mood:
        # User specified what they want to feel
        target_emotion = parse_emotion(desired_mood)
    elif user_emotions:
        # Use average of user's past emotions
        target_emotion = average_vectors(user_emotions)
    else:
        # Default to neutral/calm for brand new users
        target_emotion = (0.1, 0.3)
    
    recommender = EmotionalRecommender()
    
    if mode == "opposite":
        # Recommend opposite emotions (for mood change)
        recommendations = recommender.recommend_opposite(
            current_emotion=target_emotion,
            media_type=media_type,
            top_k=limit
        )
    else:
        recommendations = recommender.recommend(
            target_emotion=target_emotion,
            user_id=user_id,
            media_type=media_type,
            top_k=limit
        )
    
    return recommendations


def get_user_emotion_history(user_id: str, limit: int = 50):
    """
    Get user's emotion history from database.
    
    Args:
        user_id: User's unique ID
        limit: Maximum number of emotions to return
        
    Returns:
        List of emotion records
    """
    emotions = get_user_emotions_from_db(user_id)
    
    # Format for API response
    formatted = []
    for e in emotions[:limit]:
        formatted.append({
            "id": e[0],
            "media_id": e[1],
            "media_type": e[2],
            "emotion": {
                "valence": e[3],
                "arousal": e[4]
            },
            "emotion_text": e[5],
            "created_at": e[6].isoformat() if e[6] else None
        })
    
    return formatted


def analyze_user_emotions(user_id: str):
    """
    Analyze user's emotional patterns over time.
    
    Args:
        user_id: User's unique ID
        
    Returns:
        Dictionary with emotional analysis
    """
    emotions = get_user_emotions_from_db(user_id)
    
    if not emotions:
        return {
            "has_data": False,
            "message": "No emotion data available"
        }
    
    valences = [e[3] for e in emotions if e[3] is not None]
    arousals = [e[4] for e in emotions if e[4] is not None]
    
    avg_emotion = get_average_user_emotion(user_id)
    
    analysis = {
        "has_data": True,
        "total_emotions": len(emotions),
        "average_emotion": {
            "valence": avg_emotion[0] if avg_emotion else 0,
            "arousal": avg_emotion[1] if avg_emotion else 0,
            "description": _describe_emotion(avg_emotion) if avg_emotion else "Neutral"
        },
        "emotional_range": {
            "valence": {
                "min": round(min(valences), 3),
                "max": round(max(valences), 3),
                "range": round(max(valences) - min(valences), 3)
            },
            "arousal": {
                "min": round(min(arousals), 3),
                "max": round(max(arousals), 3),
                "range": round(max(arousals) - min(arousals), 3)
            }
        },
        "dominant_quadrant": _get_dominant_quadrant(valences, arousals)
    }
    
    return analysis


def _describe_emotion(emotion: Tuple[float, float]) -> str:
    """Helper to describe emotion in words"""
    valence, arousal = emotion
    
    if valence > 0.5 and arousal > 0.6:
        return "Happy and Energetic"
    elif valence > 0.5 and arousal <= 0.6:
        return "Content and Calm"
    elif valence <= -0.3 and arousal > 0.6:
        return "Intense and Anxious"
    elif valence <= -0.3 and arousal <= 0.6:
        return "Sad and Low Energy"
    else:
        return "Neutral"


def _get_dominant_quadrant(valences, arousals) -> str:
    # Count emotions in each quadrant
    q1 = sum(1 for v, a in zip(valences, arousals) if v > 0 and a > 0.5)  # Happy
    q2 = sum(1 for v, a in zip(valences, arousals) if v <= 0 and a > 0.5)  # Anxious
    q3 = sum(1 for v, a in zip(valences, arousals) if v <= 0 and a <= 0.5)  # Sad
    q4 = sum(1 for v, a in zip(valences, arousals) if v > 0 and a <= 0.5)  # Calm
    
    quadrants = {
        "Happy/Energetic": q1,
        "Intense/Anxious": q2,
        "Sad/Low Energy": q3,
        "Calm/Content": q4
    }
    
    return max(quadrants, key=quadrants.get)