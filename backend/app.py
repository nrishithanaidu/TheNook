from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, Text, Date
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import declarative_base, sessionmaker
import urllib.parse
import uuid
from datetime import datetime
import requests
import traceback

app = Flask(__name__)

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
# MODELS
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
        # Step 1: Search for movies
        search_res = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params={
                "query": query,
                "api_key": TMDB_API_KEY,
                "language": "en-US"
            },
            timeout=10
        )
        
        search_data = search_res.json()
        results = []
        
        # Step 2: Get detailed info for each result (including runtime)
        for item in search_data.get("results", [])[:5]:
            movie_id = item.get("id")
            
            # Fetch movie details to get runtime and director
            try:
                details_res = requests.get(
                    f"https://api.themoviedb.org/3/movie/{movie_id}",
                    params={
                        "api_key": TMDB_API_KEY,
                        "append_to_response": "credits"
                    },
                    timeout=5
                )
                details = details_res.json()
                
                # Get director from credits
                director = "Unknown"
                if "credits" in details and "crew" in details["credits"]:
                    directors = [crew["name"] for crew in details["credits"]["crew"] if crew["job"] == "Director"]
                    if directors:
                        director = directors[0]
                
                # Get primary genre
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
                # If details fetch fails, add basic info
                print(f"Failed to fetch details for movie {movie_id}: {e}")
                results.append({
                    "trackName": item.get("title"),
                    "artistName": "Unknown",
                    "releaseDate": item.get("release_date", ""),
                    "primaryGenreName": "Film",
                    "artworkUrl100": f"https://image.tmdb.org/t/p/w500{item['poster_path']}" if item.get("poster_path") else "",
                    "longDescription": item.get("overview", ""),
                    "trackTimeMillis": 0
                })
        
        return jsonify({"results": results})
    except Exception as e:
        print(f"Error fetching movies: {e}")
        traceback.print_exc()
        return jsonify({"results": []}), 200

# -------------------------
# MAGIC FETCH - BOOKS (Google Books via Backend)
# -------------------------
@app.route("/api/magic-book-search")
def magic_book_search():
    query = request.args.get("q")
    if not query:
        return jsonify({"items": []})

    try:
        res = requests.get(
            "https://www.googleapis.com/books/v1/volumes",
            params={
                "q": query,
                "maxResults": 5
            },
            timeout=10
        )
        return jsonify(res.json())
    except Exception as e:
        print(f"Error fetching books: {e}")
        return jsonify({"items": []}), 200

# -------------------------
# MOVIES CRUD
# -------------------------
@app.route("/api/movies", methods=["GET"])
def get_movies():
    session = SessionLocal()
    try:
        movies = session.query(Movie).all()
        return jsonify([
            {
                "id": m.id,
                "title": m.title,
                "director": m.director,
                "year": m.year,
                "genre": m.genre,
                "runtime": m.runtime,
                "status": m.status,
                "language": m.language,
                "rating": m.rating,
                "moods": m.moods or [],
                "img": m.img,
                "synopsis": m.synopsis,
                "review": m.review,
                "start_date": m.start_date.isoformat() if m.start_date else None,
                "finish_date": m.finish_date.isoformat() if m.finish_date else None
            } for m in movies
        ])
    finally:
        session.close()

@app.route("/api/movies", methods=["POST"])
def add_movie():
    session = SessionLocal()
    try:
        data = request.json
        movie = Movie(
            id=str(uuid.uuid4()),
            title=data["title"],
            director=data.get("director"),
            year=data.get("year"),
            genre=data.get("genre"),
            runtime=int(data.get("runtime", 0)) if data.get("runtime") else 0,
            status=data.get("status"),
            language=data.get("language"),
            rating=int(data.get("rating", 0)) if data.get("rating") else 0,
            moods=data.get("moods", []),
            img=data.get("img"),
            synopsis=data.get("synopsis"),
            review=data.get("review"),
            start_date=parse_date(data.get("start_date")),
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
            if key in ["start_date", "finish_date"]:
                continue
            if hasattr(movie, key):
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
        return jsonify([
            {
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "genre": b.genre,
                "status": b.status,
                "rating": b.rating,
                "moods": b.moods or [],
                "start_date": b.start_date.isoformat() if b.start_date else None,
                "finish_date": b.finish_date.isoformat() if b.finish_date else None,
                "review": b.review
            } for b in books
        ])
    finally:
        session.close()

@app.route("/api/books", methods=["POST"])
def add_book():
    session = SessionLocal()
    try:
        data = request.json
        book = Book(
            id=str(uuid.uuid4()),
            title=data["title"],
            author=data.get("author"),
            genre=data.get("genre"),
            status=data.get("status"),
            rating=int(data.get("rating", 0)) if data.get("rating") else 0,
            moods=data.get("moods", []),
            start_date=parse_date(data.get("start_date")),
            finish_date=parse_date(data.get("finish_date")),
            review=data.get("review")
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
            if key in ["start_date", "finish_date"]:
                continue
            if hasattr(book, key):
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
if __name__ == "__main__":
    app.run(debug=True)
