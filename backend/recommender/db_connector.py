

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import Config
import uuid

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(bind=engine)


def get_media_with_emotions():
    
    session = SessionLocal()
    try:
        result = session.execute(text("""
            SELECT id, title, 'movie' as media_type, moods, rating
            FROM movies
            WHERE moods IS NOT NULL AND array_length(moods, 1) > 0
            
            UNION ALL
            
            SELECT id, title, 'book' as media_type, moods, rating
            FROM books
            WHERE moods IS NOT NULL AND array_length(moods, 1) > 0
            
            UNION ALL
            
            SELECT id, title, 'podcast' as media_type, 
                    ARRAY[mood]::text[] as moods, rating
            FROM podcasts
            WHERE mood IS NOT NULL
            
            UNION ALL
            
            SELECT id, album_name as title, 'album' as media_type,
                    ARRAY[mood]::text[] as moods, rating
            FROM albums
            WHERE mood IS NOT NULL
        """))
        
        return result.fetchall()
    finally:
        session.close()


def save_user_emotion_to_db(user_id, media_id, media_type, emotion_x, emotion_y, emotion_text):
    """
    Save user's emotional response to PostgreSQL.
    
    Args:
        user_id: User's unique ID
        media_id: ID of the media item (movie, book, etc.)
        media_type: Type of media ('movie', 'book', 'podcast', 'album')
        emotion_x: Valence coordinate (-1 to 1)
        emotion_y: Arousal coordinate (0 to 1)
        emotion_text: Original text the user wrote
    """
    session = SessionLocal()
    try:
        session.execute(text("""
            INSERT INTO user_emotions 
            (id, user_id, media_id, media_type, emotion_x, emotion_y, emotion_text, created_at)
            VALUES (:id, :user_id, :media_id, :media_type, :x, :y, :text, NOW())
        """), {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "media_id": media_id,
            "media_type": media_type,
            "x": emotion_x,
            "y": emotion_y,
            "text": emotion_text
        })
        session.commit()
    finally:
        session.close()


def get_user_emotions_from_db(user_id):
    """
    Retrieve all emotion logs for a specific user from database.
    
    Args:
        user_id: User's unique ID
        
    Returns:
        List of emotion records
    """
    session = SessionLocal()
    try:
        result = session.execute(text("""
            SELECT id, media_id, media_type, emotion_x, emotion_y, 
                    emotion_text, created_at
            FROM user_emotions
            WHERE user_id = :user_id
            ORDER BY created_at DESC
        """), {"user_id": user_id})
        
        return result.fetchall()
    finally:
        session.close()


def get_average_user_emotion(user_id):
    """
    Calculate average emotion vector for a user.
    
    Args:
        user_id: User's unique ID
        
    Returns:
        Tuple (avg_valence, avg_arousal) or None if no emotions
    """
    session = SessionLocal()
    try:
        result = session.execute(text("""
            SELECT AVG(emotion_x) as avg_x, AVG(emotion_y) as avg_y
            FROM user_emotions
            WHERE user_id = :user_id
        """), {"user_id": user_id})
        
        row = result.fetchone()
        if row and row[0] is not None:
            return (round(row[0], 3), round(row[1], 3))
        return None
    finally:
        session.close()