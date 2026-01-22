from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, Text, Date, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import urllib.parse
import uuid
#from chatbot import chatbot_bp
from datetime import datetime
import requests
import traceback

app = Flask(__name__)
#app.register_blueprint(chatbot_bp)


# -------------------------
# CORS
# -------------------------
CORS(app, resources={r"/*": {"origins": "*"}})

# -------------------------
# DATABASE CONFIG
# -------------------------
user = "postgres"
password = urllib.parse.quote_plus("TheNook@Rishitha1594")
host = "db.tnogvzlpaqzzxcmplopa.supabase.co"
port = "6543"
dbname = "postgres"

DATABASE_URL = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}?sslmode=require"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# -------------------------
# MODELS - Define ALL models BEFORE creating tables
# -------------------------
class Movie(Base):
    __tablename__ = "movies"
    id = Column(String, primary_key=True)
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

class Book(Base):
    __tablename__ = "books"
    id = Column(String, primary_key=True)
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

class Podcast(Base):
    __tablename__ = "podcasts"
    id = Column(String, primary_key=True)
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
    active_episode_id = Column(String)  # Track which episode is currently playing
    # Relationship
    episodes = relationship("Episode", back_populates="podcast", cascade="all, delete-orphan")

class Episode(Base):
    __tablename__ = "episodes"
    id = Column(String, primary_key=True)
    podcast_id = Column(String, ForeignKey("podcasts.id", ondelete="CASCADE"), nullable=False)
    episode_title = Column(String, nullable=False)
    mood = Column(String)
    rating = Column(Integer)
    notes = Column(Text)
    review = Column(Text)  # Added review field
    # Relationship
    podcast = relationship("Podcast", back_populates="episodes")

class Album(Base):
    __tablename__ = "albums"
    id = Column(String, primary_key=True)
    album_name = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    status = Column(String)
    mood = Column(String)
    rating = Column(Integer)
    notes = Column(Text)
    img = Column(Text)
    genre = Column(String)
    year = Column(String)
    # Relationship
    songs = relationship("Song", back_populates="album", cascade="all, delete-orphan")

class Song(Base):
    __tablename__ = "songs"
    id = Column(String, primary_key=True)
    album_id = Column(String, ForeignKey("albums.id", ondelete="CASCADE"), nullable=False)
    song_title = Column(String, nullable=False)
    mood = Column(String)
    rating = Column(Integer)
    notes = Column(Text)
    review = Column(Text)  # Added review field
    # Relationship
    album = relationship("Album", back_populates="songs")

# Create all tables
Base.metadata.create_all(engine)

# -------------------------
# HELPERS
# -------------------------
def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return None
    
def safe_int(val, default=0):
    try:
        if val is None or str(val).strip() == "": return default
        return int(val)
    except: return default

# -------------------------
# HEALTH
# -------------------------
@app.route("/api/health")
def health():
    return jsonify({"status": "online"})

# -------------------------
# MAGIC FETCH - MOVIES (TMDB API)
# -------------------------
TMDB_API_KEY = "c1049f6f7a836087e3f3a57acbfe70f0"

@app.route("/api/magic-movie-search")
def magic_movie_search():
    query = request.args.get("q")
    if not query:
        return jsonify({"results": []})

    try:
        search_res = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params={"query": query, "api_key": TMDB_API_KEY, "language": "en-US"},
            timeout=10
        )
        
        search_data = search_res.json()
        results = []
        
        for item in search_data.get("results", [])[:5]:
            movie_id = item.get("id")
            
            try:
                details_res = requests.get(
                    f"https://api.themoviedb.org/3/movie/{movie_id}",
                    params={"api_key": TMDB_API_KEY, "append_to_response": "credits"},
                    timeout=5
                )
                details = details_res.json()
                
                director = "Unknown"
                if "credits" in details and "crew" in details["credits"]:
                    directors = [crew["name"] for crew in details["credits"]["crew"] if crew["job"] == "Director"]
                    if directors:
                        director = directors[0]
                
                genres = details.get("genres", [])
                genre = genres[0]["name"] if genres else "Film"
                
                results.append({
                    "trackName": item.get("title"),
                    "artistName": director,
                    "releaseDate": item.get("release_date", ""),
                    "primaryGenreName": genre,
                    "genre": genre,
                    "artworkUrl100": f"https://image.tmdb.org/t/p/w500{item['poster_path']}" if item.get("poster_path") else "",
                    "longDescription": item.get("overview", ""),
                    "shortDescription": item.get("overview", "")[:150] + "..." if item.get("overview") else "",
                    "trackTimeMillis": details.get("runtime", 0) * 60000 if details.get("runtime") else 0
                })
            except Exception as e:
                print(f"Failed to fetch details for movie {movie_id}: {e}")
        
        return jsonify({"results": results})
    except Exception as e:
        print(f"Error fetching movies: {e}")
        traceback.print_exc()
        return jsonify({"results": []}), 200

# -------------------------
# MAGIC FETCH - TV SHOWS
# -------------------------
@app.route("/api/magic-tv-search")
def magic_tv_search():
    query = request.args.get("q")
    if not query:
        return jsonify({"results": []})

    try:
        search_res = requests.get(
            "https://api.themoviedb.org/3/search/tv",
            params={"query": query, "api_key": TMDB_API_KEY, "language": "en-US"},
            timeout=10
        )
        
        search_data = search_res.json()
        results = []
        
        for item in search_data.get("results", [])[:5]:
            tv_id = item.get("id")
            
            try:
                details_res = requests.get(
                    f"https://api.themoviedb.org/3/tv/{tv_id}",
                    params={"api_key": TMDB_API_KEY, "append_to_response": "credits"},
                    timeout=5
                )
                details = details_res.json()
                
                creator = "Unknown"
                if details.get("created_by") and len(details["created_by"]) > 0:
                    creator = details["created_by"][0]["name"]
                
                genres = details.get("genres", [])
                genre = genres[0]["name"] if genres else "TV Show"
                
                results.append({
                    "trackName": item.get("name"),
                    "artistName": creator,
                    "releaseDate": item.get("first_air_date", ""),
                    "primaryGenreName": genre,
                    "genre": genre,
                    "artworkUrl100": f"https://image.tmdb.org/t/p/w500{item['poster_path']}" if item.get("poster_path") else "",
                    "longDescription": item.get("overview", ""),
                    "shortDescription": item.get("overview", "")[:150] + "..." if item.get("overview") else "",
                    "trackTimeMillis": details.get("episode_run_time", [45])[0] * 60000 if details.get("episode_run_time") else 2700000
                })
            except Exception as e:
                print(f"Failed to fetch TV details for {tv_id}: {e}")
        
        return jsonify({"results": results})
    except Exception as e:
        print(f"Error fetching TV shows: {e}")
        traceback.print_exc()
        return jsonify({"results": []}), 200

# -------------------------
# MAGIC FETCH - BOOKS
# -------------------------
@app.route("/api/magic-book-search")
def magic_book_search():
    query = request.args.get("q")
    if not query:
        return jsonify({"items": []})

    try:
        res = requests.get(
            "https://www.googleapis.com/books/v1/volumes",
            params={"q": query, "maxResults": 5},
            timeout=10
        )
        return jsonify(res.json())
    except Exception as e:
        print(f"Error fetching books: {e}")
        return jsonify({"items": []}), 200

# -------------------------
# MAGIC FETCH - PODCASTS
# -------------------------
@app.route("/api/magic-podcast-search")
def magic_podcast_search():
    query = request.args.get("q")
    if not query: return jsonify({"results": []})
    results = []
    
    try:
        itunes_res = requests.get("https://itunes.apple.com/search", params={"media": "podcast", "term": query, "limit": 5}, timeout=10)
        itunes_data = itunes_res.json()
        for item in itunes_data.get("results", []):
            try:
                ep_res = requests.get("https://itunes.apple.com/lookup", params={"id": item.get("collectionId"), "entity": "podcastEpisode", "limit": 10}, timeout=5)
                ep_data = ep_res.json()
                episodes = [{"episode_title": e.get("trackName"), "mood": "", "rating": 0, "notes": ""} for e in ep_data.get("results", []) if e.get("wrapperType") == "podcastEpisode"]
            except:
                episodes = []
            
            results.append({
                "title": item.get("collectionName"),
                "host": item.get("artistName"),
                "artwork": item.get("artworkUrl600"),
                "type": "Podcast",
                "genre": item.get("primaryGenreName"),
                "episodes": episodes[:10]
            })
    except: pass

    return jsonify({"results": results})

# -------------------------
# MAGIC FETCH - MUSIC
# -------------------------
@app.route("/api/magic-music-search")
def magic_music_search():
    query = request.args.get("q")
    if not query: return jsonify({"results": []})
    try:
        res = requests.get("https://itunes.apple.com/search", params={"media": "music", "entity": "album", "term": query, "limit": 5}, timeout=10)
        data = res.json()
        results = []
        for item in data.get("results", []):
            album_id = item.get("collectionId")
            try:
                track_res = requests.get("https://itunes.apple.com/lookup", params={"id": album_id, "entity": "song"}, timeout=5)
                track_data = track_res.json()
                songs = [{"song_title": t.get("trackName"), "mood": "", "rating": 0, "notes": ""} for t in track_data.get("results", []) if t.get("wrapperType") == "track"]
            except:
                songs = []
            
            results.append({
                "album_name": item.get("collectionName"),
                "artist": item.get("artistName"),
                "artwork": item.get("artworkUrl100", "").replace("100x100bb", "600x600bb"),
                "genre": item.get("primaryGenreName"),
                "year": item.get("releaseDate", "")[:4] if item.get("releaseDate") else "",
                "songs": songs
            })
        return jsonify({"results": results})
    except: 
        return jsonify({"results": []}), 200

# -------------------------
# MOVIES CRUD
# -------------------------
@app.route("/api/movies", methods=["GET"])
def get_movies():
    session = SessionLocal()
    try:
        movies = session.query(Movie).all()
        return jsonify([{
            "id": m.id, "title": m.title, "director": m.director, "year": m.year,
            "genre": m.genre, "runtime": m.runtime, "status": m.status, "language": m.language,
            "rating": m.rating, "moods": m.moods or [], "img": m.img, "synopsis": m.synopsis,
            "review": m.review, "start_date": m.start_date.isoformat() if m.start_date else None,
            "finish_date": m.finish_date.isoformat() if m.finish_date else None
        } for m in movies])
    finally:
        session.close()

@app.route("/api/movies", methods=["POST"])
def add_movie():
    session = SessionLocal()
    try:
        data = request.json
        movie = Movie(
            id=str(uuid.uuid4()), title=data["title"], director=data.get("director"),
            year=data.get("year"), genre=data.get("genre"),
            runtime=int(data.get("runtime", 0)) if data.get("runtime") else 0,
            status=data.get("status"), language=data.get("language"),
            rating=int(data.get("rating", 0)) if data.get("rating") else 0,
            moods=data.get("moods", []), img=data.get("img"), synopsis=data.get("synopsis"),
            review=data.get("review"), start_date=parse_date(data.get("start_date")),
            finish_date=parse_date(data.get("finish_date"))
        )
        session.add(movie)
        session.commit()
        return jsonify({"message": "Movie added"}), 201
    except Exception as e:
        session.rollback()
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@app.route("/api/movies/<id>", methods=["PATCH"])
def update_movie(id):
    session = SessionLocal()
    try:
        movie = session.query(Movie).filter(Movie.id == id).first()
        if not movie:
            return jsonify({"error": "Not found"}), 404
        data = request.json
        for key, value in data.items():
            if key not in ["start_date", "finish_date"] and hasattr(movie, key):
                setattr(movie, key, value)
        movie.start_date = parse_date(data.get("start_date"))
        movie.finish_date = parse_date(data.get("finish_date"))
        session.commit()
        return jsonify({"message": "Updated"})
    finally:
        session.close()

@app.route("/api/movies/<id>", methods=["DELETE"])
def delete_movie(id):
    session = SessionLocal()
    try:
        movie = session.query(Movie).filter(Movie.id == id).first()
        if not movie:
            return jsonify({"error": "Not found"}), 404
        session.delete(movie)
        session.commit()
        return jsonify({"message": "Deleted"})
    finally:
        session.close()

# -------------------------
# BOOKS CRUD
# -------------------------
@app.route("/api/books", methods=["GET"])
def get_books():
    session = SessionLocal()
    try:
        books = session.query(Book).all()
        return jsonify([{
            "id": b.id, "title": b.title, "author": b.author, "genre": b.genre,
            "status": b.status, "rating": b.rating, "moods": b.moods or [],
            "start_date": b.start_date.isoformat() if b.start_date else None,
            "finish_date": b.finish_date.isoformat() if b.finish_date else None,
            "cover_url": b.cover_url, "review": b.review
        } for b in books])
    finally:
        session.close()

@app.route("/api/books", methods=["POST"])
def add_book():
    session = SessionLocal()
    try:
        data = request.json
        book = Book(
            id=str(uuid.uuid4()), title=data["title"], author=data.get("author"),
            genre=data.get("genre"), cover_url=data.get("cover_url"), 
            status=data.get("status"),
            rating=int(data.get("rating", 0)) if data.get("rating") else 0,
            moods=data.get("moods", []), start_date=parse_date(data.get("start_date")),
            finish_date=parse_date(data.get("finish_date")), review=data.get("review")
        )
        session.add(book)
        session.commit()
        return jsonify({"message": "Book added"}), 201
    except Exception as e:
        session.rollback()
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@app.route("/api/books/<id>", methods=["PATCH"])
def update_book(id):
    session = SessionLocal()
    try:
        book = session.query(Book).filter(Book.id == id).first()
        if not book:
            return jsonify({"error": "Not found"}), 404
        data = request.json
        for key, value in data.items():
            if key not in ["start_date", "finish_date"] and hasattr(book, key):
                setattr(book, key, value)
        book.start_date = parse_date(data.get("start_date"))
        book.finish_date = parse_date(data.get("finish_date"))
        session.commit()
        return jsonify({"message": "Updated"})
    finally:
        session.close()

@app.route("/api/books/<id>", methods=["DELETE"])
def delete_book(id):
    session = SessionLocal()
    try:
        book = session.query(Book).filter(Book.id == id).first()
        if not book:
            return jsonify({"error": "Not found"}), 404
        session.delete(book)
        session.commit()
        return jsonify({"message": "Deleted"})
    finally:
        session.close()

# -------------------------
# PODCASTS CRUD (with separate Episodes table)
# -------------------------
@app.route("/api/podcasts", methods=["GET"])
def get_podcasts():
    session = SessionLocal()
    try:
        podcasts = session.query(Podcast).all()
        return jsonify([{
            "id": p.id, "title": p.title, "host": p.host, "type": p.type,
            "status": p.status, "duration": p.duration, "mood": p.mood, 
            "rating": p.rating, "notes": p.notes,
            "date_performed": p.date_performed.isoformat() if p.date_performed else None,
            "img": p.img, "genre": p.genre, "year": p.year,
            "active_episode_id": p.active_episode_id,
            "episodes": [{
                "id": e.id, "episode_title": e.episode_title, 
                "mood": e.mood, "rating": e.rating, "notes": e.notes, "review": e.review
            } for e in p.episodes]
        } for p in podcasts])
    finally: 
        session.close()

@app.route("/api/podcasts", methods=["POST"])
def add_podcast():
    session = SessionLocal()
    try:
        data = request.json
        podcast_id = str(uuid.uuid4())
        
        new_podcast = Podcast(
            id=podcast_id, 
            title=data["title"], 
            host=data.get("host"),
            type=data.get("type", "Podcast"), 
            status=data.get("status", "upcoming"),
            duration=data.get("meta"),
            mood=data.get("mood"), 
            rating=safe_int(data.get("rating")),
            notes=data.get("notes"), 
            date_performed=parse_date(data.get("date")),
            img=data.get("img"), 
            genre=data.get("genre"), 
            year=data.get("year")
        )
        
        # Add episodes
        if "episodes" in data and data["episodes"]:
            for ep_data in data["episodes"]:
                if ep_data.get("episode_title"):  # Only add if title exists
                    new_episode = Episode(
                        id=str(uuid.uuid4()),
                        podcast_id=podcast_id,
                        episode_title=ep_data["episode_title"],
                        mood=ep_data.get("mood"),
                        rating=safe_int(ep_data.get("rating")),
                        notes=ep_data.get("notes"),
                        review=ep_data.get("review")
                    )
                    new_podcast.episodes.append(new_episode)
        
        session.add(new_podcast)
        session.commit()
        return jsonify({"message": "Podcast saved"}), 201
    except Exception as e:
        session.rollback()
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally: 
        session.close()

@app.route("/api/podcasts/<id>", methods=["PATCH"])
def update_podcast(id):
    session = SessionLocal()
    try:
        podcast = session.query(Podcast).filter(Podcast.id == id).first()
        if not podcast: 
            return jsonify({"error": "Not found"}), 404
        
        data = request.json

        
        if data.get("status") == "now-playing":
            session.query(Podcast).filter(Podcast.status == "now-playing", Podcast.id != id).update({"status": "upcoming"})
        
        
        # Update podcast fields
        for key in ["title", "host", "type", "status", "mood", "notes", "img", "genre", "year", "active_episode_id"]:
            if key in data: 
                setattr(podcast, key, data[key])
        
        if "meta" in data: 
            podcast.duration = data["meta"]
        if "date" in data: 
            podcast.date_performed = parse_date(data["date"])
        if "rating" in data: 
            podcast.rating = safe_int(data["rating"])
        
        # Update episodes - delete old ones and add new ones
        if "episodes" in data:
            # Delete existing episodes
            session.query(Episode).filter(Episode.podcast_id == id).delete()
            
            # Add new episodes
            for ep_data in data["episodes"]:
                if ep_data.get("episode_title"):
                    new_episode = Episode(
                        id=str(uuid.uuid4()),
                        podcast_id=id,
                        episode_title=ep_data["episode_title"],
                        mood=ep_data.get("mood"),
                        rating=safe_int(ep_data.get("rating")),
                        notes=ep_data.get("notes"),
                        review=ep_data.get("review")
                    )
                    session.add(new_episode)
        
        session.commit()
        return jsonify({"message": "Updated"})
    except Exception as e:
        session.rollback()
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally: 
        session.close()

@app.route("/api/podcasts/<id>", methods=["DELETE"])
def delete_podcast(id):
    session = SessionLocal()
    try:
        podcast = session.query(Podcast).filter(Podcast.id == id).first()
        if not podcast: 
            return jsonify({"error": "Not found"}), 404
        session.delete(podcast)  # Episodes will be deleted automatically due to cascade
        session.commit()
        return jsonify({"message": "Deleted"})
    except Exception as e:
        session.rollback()
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally: 
        session.close()

# -------------------------
# ALBUMS CRUD (with separate Songs table)
# -------------------------
@app.route("/api/albums", methods=["GET"])
def get_albums():
    session = SessionLocal()
    try:
        albums = session.query(Album).all()
        return jsonify([{
            "id": a.id, 
            "album_name": a.album_name,
            "artist": a.artist, 
            "status": a.status or "queued",
            "mood": a.mood, 
            "rating": a.rating, 
            "notes": a.notes, 
            "img": a.img,
            "genre": a.genre,
            "year": a.year,
            "songs": [{
                "id": s.id,
                "song_title": s.song_title,
                "mood": s.mood,
                "rating": s.rating,
                "notes": s.notes,
                "review": s.review
            } for s in a.songs]
        } for a in albums])
    finally:
        session.close()

@app.route("/api/albums", methods=["POST"])
def add_album():
    session = SessionLocal()
    try:
        data = request.json
        album_id = str(uuid.uuid4())
        
        new_album = Album(
            id=album_id,
            album_name=data["album_name"],
            artist=data["artist"],
            status=data.get("status", "queued"),
            mood=data.get("mood"),
            rating=safe_int(data.get("rating")),
            notes=data.get("notes"),
            img=data.get("img"),
            genre=data.get("genre"),
            year=data.get("year")
        )
        
        # Add songs
        if "songs" in data and data["songs"]:
            for song_data in data["songs"]:
                if song_data.get("song_title"):  # Only add if title exists
                    new_song = Song(
                        id=str(uuid.uuid4()),
                        album_id=album_id,
                        song_title=song_data["song_title"],
                        mood=song_data.get("mood"),
                        rating=safe_int(song_data.get("rating")),
                        notes=song_data.get("notes"),
                        review=song_data.get("review")
                    )
                    new_album.songs.append(new_song)
        
        session.add(new_album)
        session.commit()
        return jsonify({"message": "Album saved"}), 201
    except Exception as e:
        session.rollback()
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@app.route("/api/albums/<id>", methods=["PATCH"])
def update_album(id):
    session = SessionLocal()
    try:
        album = session.query(Album).filter(Album.id == id).first()
        if not album: 
            return jsonify({"error": "Not found"}), 404
        
        data = request.json
        
        # Update album fields
        for key in ["album_name", "artist", "status", "mood", "notes", "img", "genre", "year"]:
            if key in data: 
                setattr(album, key, data[key])
        
        if "rating" in data: 
            album.rating = safe_int(data["rating"])
        
        # Update songs - delete old ones and add new ones
        if "songs" in data:
            # Delete existing songs
            session.query(Song).filter(Song.album_id == id).delete()
            
            # Add new songs
            for song_data in data["songs"]:
                if song_data.get("song_title"):
                    new_song = Song(
                        id=str(uuid.uuid4()),
                        album_id=id,
                        song_title=song_data["song_title"],
                        mood=song_data.get("mood"),
                        rating=safe_int(song_data.get("rating")),
                        notes=song_data.get("notes"),
                        review=song_data.get("review")
                    )
                    session.add(new_song)
        
        session.commit()
        return jsonify({"message": "Updated"})
    except Exception as e:
        session.rollback()
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@app.route("/api/albums/<id>", methods=["DELETE"])
def delete_album(id):
    session = SessionLocal()
    try:
        album = session.query(Album).filter(Album.id == id).first()
        if not album: 
            return jsonify({"error": "Not found"}), 404
        session.delete(album)  # Songs will be deleted automatically due to cascade
        session.commit()
        return jsonify({"message": "Deleted"})
    except Exception as e:
        session.rollback()
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

# -------------------------
if __name__ == "__main__":
    app.run(debug=True)
