from sqlalchemy import create_engine, Column, Integer, String, Text, Date, ForeignKey, DateTime, Boolean, Float
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from datetime import datetime
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Base
Base = declarative_base()

# Initialize Engine and Session here to avoid circular imports in routes.py and app.py
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, **Config.SQLALCHEMY_ENGINE_OPTIONS)
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String)
    alias = Column(String)
    phone = Column(String)
    location = Column(String)
    website = Column(String)
    bio = Column(Text)
    avatar_url = Column(Text)
    genres = Column(ARRAY(String), default=[])
    interests = Column(ARRAY(String), default=[])
    notif_email = Column(Boolean, default=True)
    show_stats = Column(Boolean, default=True)
    public_profile = Column(Boolean, default=False)
    
    # Relationships
    movies = relationship("Movie", back_populates="user", cascade="all, delete-orphan")
    books = relationship("Book", back_populates="user", cascade="all, delete-orphan")
    podcasts = relationship("Podcast", back_populates="user", cascade="all, delete-orphan")
    albums = relationship("Album", back_populates="user", cascade="all, delete-orphan")
    collections = relationship("Collection", back_populates="user", cascade="all, delete-orphan")
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password matches hash"""
        return check_password_hash(self.password_hash, password)

class Movie(Base):
    __tablename__ = "movies"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    director = Column(String)
    year = Column(String)
    genre = Column(String)
    runtime = Column(Integer)
    status = Column(String)
    language = Column(String)
    rating = Column(Integer)
    moods = Column(ARRAY(String))
    img = Column(Text)
    synopsis = Column(Text)
    review = Column(Text)
    start_date = Column(Date)
    finish_date = Column(Date)
    
    user = relationship("User", back_populates="movies")

class Book(Base):
    __tablename__ = "books"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    author = Column(String)
    genre = Column(String)
    status = Column(String)
    rating = Column(Integer)
    moods = Column(ARRAY(String))
    start_date = Column(Date)
    finish_date = Column(Date)
    review = Column(Text)
    cover_url = Column(Text)
    
    user = relationship("User", back_populates="books")

class Podcast(Base):
    __tablename__ = "podcasts"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    host = Column(String)
    type = Column(String)
    status = Column(String)
    duration = Column(String)
    mood = Column(String)
    rating = Column(Integer)
    notes = Column(Text)
    date_performed = Column(Date)
    img = Column(Text)
    genre = Column(String)
    year = Column(String)
    active_episode_id = Column(String)
    
    user = relationship("User", back_populates="podcasts")
    episodes = relationship("Episode", back_populates="podcast", cascade="all, delete-orphan")

class Episode(Base):
    __tablename__ = "episodes"
    id = Column(String, primary_key=True)
    podcast_id = Column(String, ForeignKey("podcasts.id", ondelete="CASCADE"), nullable=False)
    episode_title = Column(String, nullable=False)
    mood = Column(String)
    rating = Column(Integer)
    notes = Column(Text)
    review = Column(Text)
    
    podcast = relationship("Podcast", back_populates="episodes")

class Album(Base):
    __tablename__ = "albums"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    album_name = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    status = Column(String)
    mood = Column(String)
    rating = Column(Integer)
    notes = Column(Text)
    img = Column(Text)
    genre = Column(String)
    year = Column(String)
    
    user = relationship("User", back_populates="albums")
    songs = relationship("Song", back_populates="album", cascade="all, delete-orphan")

class Song(Base):
    __tablename__ = "songs"
    id = Column(String, primary_key=True)
    album_id = Column(String, ForeignKey("albums.id", ondelete="CASCADE"), nullable=False)
    song_title = Column(String, nullable=False)
    mood = Column(String)
    rating = Column(Integer)
    notes = Column(Text)
    review = Column(Text)
    
    album = relationship("Album", back_populates="songs")

class Collection(Base):
    __tablename__ = "collections"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    media_type = Column(String, nullable=False)
    
    user = relationship("User", back_populates="collections")
    items = relationship("CollectionItem", back_populates="collection", cascade="all, delete-orphan")

class CollectionItem(Base):
    __tablename__ = "collection_items"
    id = Column(String, primary_key=True)
    collection_id = Column(String, ForeignKey("collections.id", ondelete="CASCADE"), nullable=False)
    item_id = Column(String, nullable=False)
    note = Column(Text)
    
    collection = relationship("Collection", back_populates="items")

class UserEmotion(Base):
    """
    Stores user's emotional responses to media for recommendation engine.
    Uses 2D emotion space: valence (x-axis) and arousal (y-axis)
    """
    __tablename__ = "user_emotions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    media_id = Column(String, nullable=False)
    media_type = Column(String, nullable=False)
    emotion_x = Column(Float, nullable=False)
    emotion_y = Column(Float, nullable=False)
    emotion_text = Column(Text)
    
    user = relationship("User", backref="emotions")
    
    def __repr__(self):
        return f"<UserEmotion(user={self.user_id}, media={self.media_id}, emotion=({self.emotion_x}, {self.emotion_y}))>"