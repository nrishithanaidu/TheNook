from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, Text, Date
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import declarative_base, sessionmaker
import urllib.parse
import uuid
from datetime import datetime
import traceback

app = Flask(__name__)

# -------------------------
# 🛠️ CORS CONFIGURATION
# -------------------------
# Allowing all origins and methods to prevent connection errors
# Specifically handling the 'null' origin which often happens with local HTML files
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True, methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"])

# -------------------------
# 🛠️ DATABASE CONFIGURATION
# -------------------------
user = "postgres"
password = urllib.parse.quote_plus("TheNook@Rishitha1594")
host = "db.tnogvzlpaqzzxcmplopa.supabase.co"
port = "6543" 
dbname = "postgres"

DATABASE_URL = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}?sslmode=require"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       
    pool_recycle=300,         
    connect_args={'connect_timeout': 30} 
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# -------------------------
# 📚 BOOK MODEL
# -------------------------
class Book(Base):
    __tablename__ = "books"

    # ID as String(100) is perfect for UUIDs. Ensure the DB column is type 'text' or 'varchar'.
    id = Column(String(100), primary_key=True)
    title = Column(String(200), nullable=False)
    author = Column(String(150))
    genre = Column(String(100))
    rating = Column(Integer)
    review = Column(Text)
    moods = Column(ARRAY(String))      
    status = Column(String(20))      # tbr | current | finished
    start_date = Column(Date)
    finish_date = Column(Date)

# -------------------------
# INITIALIZE DB
# -------------------------
try:
    Base.metadata.create_all(engine)
    print("✅ DATABASE CONNECTION CHECK: Success.")
except Exception as e:
    print(f"❌ DATABASE CONNECTION ERROR: {e}")

# -------------------------
# 🚀 ROUTES
# -------------------------

@app.before_request
def log_request():
    print(f"📡 {request.method} request to {request.path}")

@app.route("/")
def home():
    return "The Nook backend is alive 🕯️"

@app.route("/api/books", methods=["GET"])
def get_books():
    session = SessionLocal()
    try:
        books = session.query(Book).all()
        return jsonify([
            {
                "id": str(b.id),
                "title": b.title,
                "author": b.author,
                "genre": b.genre,
                "status": b.status,
                "rating": b.rating,
                "review": b.review,
                "moods": b.moods if b.moods else [],
                "start_date": b.start_date.isoformat() if b.start_date else None,
                "finish_date": b.finish_date.isoformat() if b.finish_date else None
            }
            for b in books
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@app.route("/api/books", methods=["POST"])
def add_book():
    session = SessionLocal()
    try:
        data = request.json
        
        def parse_date(date_str):
            if not date_str or date_str == "": return None
            try: return datetime.strptime(date_str, '%Y-%m-%d').date()
            except: return None

        # Automatically generate a UUID if one isn't provided
        book_id = data.get('id') or str(uuid.uuid4())

        new_book = Book(
            id=book_id,
            title=data.get('title', 'Untitled'),
            author=data.get('author'),
            genre=data.get('genre'),
            moods=data.get('moods', []),
            rating=int(data.get('rating', 0)) if data.get('rating') else 0,
            review=data.get('review'),
            status=data.get('status', 'tbr'),
            start_date=parse_date(data.get('start_date')),
            finish_date=parse_date(data.get('finish_date'))
        )
        
        session.add(new_book)
        session.commit()
        return jsonify({"message": f"Successfully added '{new_book.title}'", "id": new_book.id}), 201
    except Exception as e:
        session.rollback()
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@app.route("/api/books/<book_id>", methods=["PATCH"])
def update_book(book_id):
    session = SessionLocal()
    try:
        data = request.json
        book = session.query(Book).filter(Book.id == str(book_id)).first()
        if not book: return jsonify({"error": "Book not found"}), 404
        
        def parse_date(date_str):
            if not date_str or date_str == "": return None
            try: return datetime.strptime(date_str, '%Y-%m-%d').date()
            except: return None

        if 'title' in data: book.title = data['title']
        if 'author' in data: book.author = data['author']
        if 'genre' in data: book.genre = data['genre']
        if 'rating' in data: book.rating = int(data['rating']) if data['rating'] else 0
        if 'review' in data: book.review = data['review']
        if 'moods' in data: book.moods = data['moods']
        if 'status' in data: book.status = data['status']
        if 'start_date' in data: book.start_date = parse_date(data['start_date'])
        if 'finish_date' in data: book.finish_date = parse_date(data['finish_date'])
        
        session.commit()
        return jsonify({"message": f"Successfully updated '{book.title}'"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@app.route("/api/books/<book_id>", methods=["DELETE"])
def delete_book(book_id):
    session = SessionLocal()
    try:
        book = session.query(Book).filter(Book.id == str(book_id)).first()
        if not book: return jsonify({"error": "Book not found"}), 404
        
        title = book.title
        session.delete(book)
        session.commit()
        return jsonify({"message": f"Successfully deleted '{title}'"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
