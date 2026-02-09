from flask import Blueprint, jsonify, request
from models import SessionLocal, Movie, Book, Podcast, Episode, Album, Song, Collection, CollectionItem, User
from config import Config
import uuid
import requests
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from sqlalchemy.exc import SQLAlchemyError

api_bp = Blueprint('api', __name__)

# -------------------------
# HELPERS
# -------------------------
def parse_date(date_str):
    if not date_str: return None
    try: return datetime.strptime(date_str, "%Y-%m-%d").date()
    except: return None

def safe_int(val, default=0):
    try:
        if val is None or str(val).strip() == "": return default
        return int(val)
    except: return default

def validate_email(email):
    """Basic email validation"""
    return email and '@' in email and len(email) > 3

# -------------------------
# AUTH ROUTES
# -------------------------
@api_bp.route("/auth/register", methods=["POST"])
def register():
    session = SessionLocal()
    try:
        data = request.json
        
        # Validation
        if not data.get('email') or not validate_email(data['email']):
            return jsonify({"error": "Valid email required"}), 400
        if not data.get('password') or len(data['password']) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        
        # Check if user exists
        if session.query(User).filter(User.email == data['email']).first():
            return jsonify({"error": "Email already registered"}), 400
        
        # Create user with hashed password
        user_id = str(uuid.uuid4())
        new_user = User(
            id=user_id,
            email=data['email'],
            full_name=data.get('full_name'),
            alias=data.get('alias')
        )
        new_user.set_password(data['password'])  # Hash password
        
        session.add(new_user)
        session.commit()
        
        token = create_access_token(identity=user_id)
        return jsonify({
            "token": token,
            "user": {
                "id": user_id,
                "email": data['email'],
                "full_name": data.get('full_name'),
                "alias": data.get('alias')
            }
        }), 201
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@api_bp.route("/auth/login", methods=["POST"])
def login():
    session = SessionLocal()
    try:
        data = request.json
        
        if not data.get('email') or not data.get('password'):
            return jsonify({"error": "Email and password required"}), 400
        
        user = session.query(User).filter(User.email == data['email']).first()
        
        # Check password using hash
        if user and user.check_password(data['password']):
            token = create_access_token(identity=user.id)
            return jsonify({
                "token": token,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "alias": user.alias
                }
            }), 200
        
        return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": "Login failed"}), 500
    finally:
        session.close()

@api_bp.route("/auth/me", methods=["GET", "PATCH", "DELETE"])
@jwt_required()
def manage_me():
    session = SessionLocal()
    try:
        user_id = get_jwt_identity()
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        if request.method == "GET":
            return jsonify({
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "alias": user.alias,
                "phone": user.phone,
                "location": user.location,
                "website": user.website,
                "bio": user.bio,
                "avatar_url": user.avatar_url,
                "genres": user.genres,
                "interests": user.interests,
                "notif_email": user.notif_email,
                "show_stats": user.show_stats,
                "public_profile": user.public_profile,
            }), 200
        
        if request.method == "PATCH":
            data = request.json
            # Prevent updating sensitive fields
            restricted_fields = ['id', 'password_hash']
            
            for key in data:
                if key in restricted_fields:
                    continue
                if hasattr(user, key):
                    setattr(user, key, data[key])
            
            session.commit()
            return jsonify({"message": "Profile updated successfully"}), 200
        
        if request.method == "DELETE":
            # Verify password before deletion
            data = request.json
            if not data or not data.get('password'):
                return jsonify({"error": "Password is required to delete account"}), 400
            
            if not user.check_password(data['password']):
                return jsonify({"error": "Password is incorrect"}), 401
            
            # Delete user (cascade will delete all their data)
            session.delete(user)
            session.commit()
            
            return jsonify({"message": "Account deleted successfully"}), 200
    except SQLAlchemyError:
        session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@api_bp.route("/auth/password", methods=["PATCH"])
@jwt_required()
def change_password():
    session = SessionLocal()
    try:
        user_id = get_jwt_identity()
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        data = request.json
        
        # Validate required fields
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({"error": "Current password and new password are required"}), 400
        
        # Verify current password
        if not user.check_password(data['current_password']):
            return jsonify({"error": "Current password is incorrect"}), 401
        
        # Validate new password
        if len(data['new_password']) < 6:
            return jsonify({"error": "New password must be at least 6 characters"}), 400
        
        # Update password
        user.set_password(data['new_password'])
        session.commit()
        
        return jsonify({"message": "Password updated successfully"}), 200
    except SQLAlchemyError:
        session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

# -------------------------
# STATISTICS (For Homepage)
# -------------------------
@api_bp.route("/stats")
@jwt_required()
def get_stats():
    session = SessionLocal()
    try:
        user_id = get_jwt_identity()
        
        # Get user-specific stats
        movies_count = session.query(Movie).filter(Movie.user_id == user_id).count()
        books_count = session.query(Book).filter(Book.user_id == user_id).count()
        podcasts_count = session.query(Podcast).filter(Podcast.user_id == user_id).count()
        albums_count = session.query(Album).filter(Album.user_id == user_id).count()
        
        # Calculate average rating across all rated items
        from sqlalchemy import func
        movie_avg = session.query(func.avg(Movie.rating)).filter(
            Movie.user_id == user_id, Movie.rating.isnot(None), Movie.rating > 0
        ).scalar() or 0
        book_avg = session.query(func.avg(Book.rating)).filter(
            Book.user_id == user_id, Book.rating.isnot(None), Book.rating > 0
        ).scalar() or 0
        
        avg_rating = round((movie_avg + book_avg) / 2, 1) if (movie_avg or book_avg) else 0
        
        stats = {
            "movies": movies_count,
            "books": books_count,
            "podcasts": podcasts_count,
            "albums": albums_count,
            "avg_rating": avg_rating
        }
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

# -------------------------
# MOVIES CRUD
# -------------------------
@api_bp.route("/movies", methods=["GET", "POST"])
@jwt_required()
def manage_movies():
    session = SessionLocal()
    user_id = get_jwt_identity()
    
    try:
        if request.method == "GET":
            # Only get current user's movies
            movies = session.query(Movie).filter(Movie.user_id == user_id).all()
            res = []
            for m in movies:
                res.append({
                    "id": m.id,
                    "title": m.title,
                    "director": m.director,
                    "year": m.year,
                    "genre": m.genre,
                    "runtime": m.runtime,
                    "status": m.status,
                    "language": m.language,
                    "rating": m.rating,
                    "moods": m.moods,
                    "img": m.img,
                    "synopsis": m.synopsis,
                    "review": m.review,
                    "start_date": str(m.start_date) if m.start_date else None,
                    "finish_date": str(m.finish_date) if m.finish_date else None
                })
            return jsonify(res), 200
        
        if request.method == "POST":
            data = request.json
            
            if not data.get('title'):
                return jsonify({"error": "Title is required"}), 400
            
            new_movie = Movie(
                id=str(uuid.uuid4()),
                user_id=user_id,  # Associate with current user
                title=data['title'],
                director=data.get('director'),
                year=data.get('year'),
                genre=data.get('genre'),
                runtime=safe_int(data.get('runtime')),
                status=data.get('status'),
                language=data.get('language'),
                rating=safe_int(data.get('rating')),
                moods=data.get('moods', []),
                img=data.get('img'),
                synopsis=data.get('synopsis'),
                review=data.get('review'),
                start_date=parse_date(data.get('start_date')),
                finish_date=parse_date(data.get('finish_date'))
            )
            session.add(new_movie)
            session.commit()
            return jsonify({"message": "Movie logged successfully", "id": new_movie.id}), 201
    except SQLAlchemyError:
        session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@api_bp.route("/movies/<id>", methods=["GET", "PATCH", "DELETE"])
@jwt_required()
def update_movie(id):
    session = SessionLocal()
    user_id = get_jwt_identity()
    
    try:
        # Ensure user can only access their own movies
        movie = session.query(Movie).filter(Movie.id == id, Movie.user_id == user_id).first()
        
        if not movie:
            return jsonify({"error": "Movie not found"}), 404
        
        if request.method == "GET":
            return jsonify({
                "id": movie.id,
                "title": movie.title,
                "director": movie.director,
                "year": movie.year,
                "genre": movie.genre,
                "runtime": movie.runtime,
                "status": movie.status,
                "language": movie.language,
                "rating": movie.rating,
                "moods": movie.moods,
                "img": movie.img,
                "synopsis": movie.synopsis,
                "review": movie.review,
                "start_date": str(movie.start_date) if movie.start_date else None,
                "finish_date": str(movie.finish_date) if movie.finish_date else None
            }), 200
        
        if request.method == "PATCH":
            data = request.json
            for key in data:
                if key in ["start_date", "finish_date"]:
                    setattr(movie, key, parse_date(data[key]))
                elif key in ["runtime", "rating"]:
                    setattr(movie, key, safe_int(data[key]))
                elif hasattr(movie, key) and key not in ['id', 'user_id']:
                    setattr(movie, key, data[key])
            session.commit()
            return jsonify({"message": "Movie updated successfully"}), 200
        
        if request.method == "DELETE":
            session.delete(movie)
            session.commit()
            return jsonify({"message": "Movie deleted successfully"}), 200
    except SQLAlchemyError:
        session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

# -------------------------
# BOOKS CRUD
# -------------------------
@api_bp.route("/books", methods=["GET", "POST"])
@jwt_required()
def manage_books():
    session = SessionLocal()
    user_id = get_jwt_identity()
    
    try:
        if request.method == "GET":
            books = session.query(Book).filter(Book.user_id == user_id).all()
            res = [{
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "genre": b.genre,
                "status": b.status,
                "rating": b.rating,
                "moods": b.moods,
                "start_date": str(b.start_date) if b.start_date else None,
                "finish_date": str(b.finish_date) if b.finish_date else None,
                "cover_url": b.cover_url,
                "review": b.review
            } for b in books]
            return jsonify(res), 200
        
        if request.method == "POST":
            data = request.json
            
            if not data.get('title'):
                return jsonify({"error": "Title is required"}), 400
            
            new_book = Book(
                id=str(uuid.uuid4()),
                user_id=user_id,
                title=data['title'],
                author=data.get('author'),
                genre=data.get('genre'),
                status=data.get('status'),
                rating=safe_int(data.get('rating')),
                moods=data.get('moods', []),
                start_date=parse_date(data.get('start_date')),
                finish_date=parse_date(data.get('finish_date')),
                cover_url=data.get('cover_url'),
                review=data.get('review')
            )
            session.add(new_book)
            session.commit()
            return jsonify({"message": "Book logged successfully", "id": new_book.id}), 201
    except SQLAlchemyError:
        session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@api_bp.route("/books/<id>", methods=["GET", "PATCH", "DELETE"])
@jwt_required()
def update_book(id):
    session = SessionLocal()
    user_id = get_jwt_identity()
    
    try:
        book = session.query(Book).filter(Book.id == id, Book.user_id == user_id).first()
        
        if not book:
            return jsonify({"error": "Book not found"}), 404
        
        if request.method == "GET":
            return jsonify({
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "genre": book.genre,
                "status": book.status,
                "rating": book.rating,
                "moods": book.moods,
                "start_date": str(book.start_date) if book.start_date else None,
                "finish_date": str(book.finish_date) if book.finish_date else None,
                "cover_url": book.cover_url,
                "review": book.review
            }), 200
        
        if request.method == "PATCH":
            data = request.json
            for key in data:
                if key in ["start_date", "finish_date"]:
                    setattr(book, key, parse_date(data[key]))
                elif key == "rating":
                    setattr(book, key, safe_int(data[key]))
                elif hasattr(book, key) and key not in ['id', 'user_id']:
                    setattr(book, key, data[key])
            session.commit()
            return jsonify({"message": "Book updated successfully"}), 200
        
        if request.method == "DELETE":
            session.delete(book)
            session.commit()
            return jsonify({"message": "Book deleted successfully"}), 200
    except SQLAlchemyError:
        session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

# -------------------------
# PODCASTS CRUD
# -------------------------
@api_bp.route("/podcasts", methods=["GET", "POST"])
@jwt_required()
def manage_podcasts():
    session = SessionLocal()
    user_id = get_jwt_identity()
    
    try:
        if request.method == "GET":
            podcasts = session.query(Podcast).filter(Podcast.user_id == user_id).all()
            res = []
            for p in podcasts:
                episodes = [{"id": e.id, "episode_title": e.episode_title, "rating": e.rating} for e in p.episodes]
                res.append({
                    "id": p.id,
                    "title": p.title,
                    "host": p.host,
                    "img": p.img,
                    "status": p.status,
                    "episodes": episodes,
                    "mood": p.mood,
                    "rating": p.rating
                })
            return jsonify(res), 200
        
        if request.method == "POST":
            data = request.json
            
            if not data.get('title'):
                return jsonify({"error": "Title is required"}), 400
            
            pod_id = str(uuid.uuid4())
            new_pod = Podcast(
                id=pod_id,
                user_id=user_id,
                title=data['title'],
                host=data.get('host'),
                type=data.get('type'),
                status=data.get('status'),
                duration=data.get('duration'),
                mood=data.get('mood'),
                rating=safe_int(data.get('rating')),
                notes=data.get('notes'),
                date_performed=parse_date(data.get('date_performed')),
                img=data.get('img'),
                genre=data.get('genre'),
                year=data.get('year'),
                active_episode_id=data.get('active_episode_id')
            )
            session.add(new_pod)
            
            # Add episodes
            for ep in data.get('episodes', []):
                if ep.get('episode_title'):
                    session.add(Episode(
                        id=str(uuid.uuid4()),
                        podcast_id=pod_id,
                        episode_title=ep['episode_title'],
                        mood=ep.get('mood'),
                        rating=safe_int(ep.get('rating')),
                        notes=ep.get('notes'),
                        review=ep.get('review')
                    ))
            
            session.commit()
            return jsonify({"message": "Podcast logged successfully", "id": pod_id}), 201
    except SQLAlchemyError:
        session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@api_bp.route("/podcasts/<id>", methods=["GET", "PATCH", "DELETE"])
@jwt_required()
def update_podcast(id):
    session = SessionLocal()
    user_id = get_jwt_identity()
    
    try:
        pod = session.query(Podcast).filter(Podcast.id == id, Podcast.user_id == user_id).first()
        
        if not pod:
            return jsonify({"error": "Podcast not found"}), 404
        
        if request.method == "GET":
            episodes = [{"id": e.id, "episode_title": e.episode_title, "rating": e.rating, "mood": e.mood, "notes": e.notes, "review": e.review} for e in pod.episodes]
            return jsonify({
                "id": pod.id,
                "title": pod.title,
                "host": pod.host,
                "type": pod.type,
                "status": pod.status,
                "duration": pod.duration,
                "mood": pod.mood,
                "rating": pod.rating,
                "notes": pod.notes,
                "date_performed": str(pod.date_performed) if pod.date_performed else None,
                "img": pod.img,
                "genre": pod.genre,
                "year": pod.year,
                "active_episode_id": pod.active_episode_id,
                "episodes": episodes
            }), 200
        
        if request.method == "PATCH":
            data = request.json
            for key in data:
                if key == "episodes":
                    continue  # Handle separately if needed
                elif key == "date_performed":
                    setattr(pod, key, parse_date(data[key]))
                elif key == "rating":
                    setattr(pod, key, safe_int(data[key]))
                elif hasattr(pod, key) and key not in ['id', 'user_id']:
                    setattr(pod, key, data[key])
            session.commit()
            return jsonify({"message": "Podcast updated successfully"}), 200
        
        if request.method == "DELETE":
            session.delete(pod)
            session.commit()
            return jsonify({"message": "Podcast deleted successfully"}), 200
    except SQLAlchemyError:
        session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

# -------------------------
# ALBUMS CRUD
# -------------------------
@api_bp.route("/albums", methods=["GET", "POST"])
@jwt_required()
def manage_albums():
    session = SessionLocal()
    user_id = get_jwt_identity()
    
    try:
        if request.method == "GET":
            albums = session.query(Album).filter(Album.user_id == user_id).all()
            res = []
            for a in albums:
                songs = [{"id": s.id, "song_title": s.song_title, "rating": s.rating, "mood": s.mood, "notes": s.notes} for s in a.songs]
                res.append({
                    "id": a.id,
                    "album_name": a.album_name,
                    "artist": a.artist,
                    "img": a.img,
                    "status": a.status,
                    "songs": songs,
                    "mood": a.mood,
                    "rating": a.rating,
                    "genre": a.genre,
                    "year": a.year
                })
            return jsonify(res), 200
        
        if request.method == "POST":
            data = request.json
            
            if not data.get('album_name') or not data.get('artist'):
                return jsonify({"error": "Album name and artist are required"}), 400
            
            alb_id = str(uuid.uuid4())
            new_alb = Album(
                id=alb_id,
                user_id=user_id,
                album_name=data['album_name'],
                artist=data['artist'],
                status=data.get('status'),
                img=data.get('img'),
                mood=data.get('mood'),
                rating=safe_int(data.get('rating')),
                notes=data.get('notes'),
                genre=data.get('genre'),
                year=data.get('year')
            )
            session.add(new_alb)
            
            # Add songs
            for s in data.get('songs', []):
                if s.get('song_title'):
                    session.add(Song(
                        id=str(uuid.uuid4()),
                        album_id=alb_id,
                        song_title=s['song_title'],
                        mood=s.get('mood'),
                        rating=safe_int(s.get('rating')),
                        notes=s.get('notes'),
                        review=s.get('review')
                    ))
            
            session.commit()
            return jsonify({"message": "Album logged successfully", "id": alb_id}), 201
    except SQLAlchemyError:
        session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@api_bp.route("/albums/<id>", methods=["GET", "PATCH", "DELETE"])
@jwt_required()
def update_album(id):
    session = SessionLocal()
    user_id = get_jwt_identity()
    
    try:
        album = session.query(Album).filter(Album.id == id, Album.user_id == user_id).first()
        
        if not album:
            return jsonify({"error": "Album not found"}), 404
        
        if request.method == "GET":
            songs = [{"id": s.id, "song_title": s.song_title, "rating": s.rating, "mood": s.mood, "notes": s.notes, "review": s.review} for s in album.songs]
            return jsonify({
                "id": album.id,
                "album_name": album.album_name,
                "artist": album.artist,
                "status": album.status,
                "mood": album.mood,
                "rating": album.rating,
                "notes": album.notes,
                "img": album.img,
                "genre": album.genre,
                "year": album.year,
                "songs": songs
            }), 200
        
        if request.method == "PATCH":
            data = request.json
            for key in data:
                if key == "songs":
                    continue  # Handle separately if needed
                elif key == "rating":
                    setattr(album, key, safe_int(data[key]))
                elif hasattr(album, key) and key not in ['id', 'user_id']:
                    setattr(album, key, data[key])
            session.commit()
            return jsonify({"message": "Album updated successfully"}), 200
        
        if request.method == "DELETE":
            session.delete(album)
            session.commit()
            return jsonify({"message": "Album deleted successfully"}), 200
    except SQLAlchemyError:
        session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

# -------------------------
# COLLECTIONS CRUD
# -------------------------
@api_bp.route("/collections", methods=["GET", "POST"])
@jwt_required()
def manage_collections():
    session = SessionLocal()
    user_id = get_jwt_identity()
    
    try:
        media_type = request.args.get("media_type")
        
        if request.method == "GET":
            query = session.query(Collection).filter(Collection.user_id == user_id)
            if media_type:
                query = query.filter(Collection.media_type == media_type)
            colls = query.all()
            
            res = []
            for c in colls:
                items = session.query(CollectionItem).filter(CollectionItem.collection_id == c.id).all()
                res.append({
                    "id": c.id,
                    "name": c.name,
                    "description": c.description,
                    "media_type": c.media_type,
                    "item_count": len(items),
                })
            return jsonify(res), 200
        
        if request.method == "POST":
            data = request.json
            
            if not data.get('name') or not data.get('media_type'):
                return jsonify({"error": "Name and media_type are required"}), 400
            
            new_coll = Collection(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=data['name'],
                description=data.get('description'),
                media_type=data['media_type']
            )
            session.add(new_coll)
            session.commit()
            return jsonify({"message": "Collection created successfully", "id": new_coll.id}), 201
    except SQLAlchemyError:
        session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@api_bp.route("/collections/<id>", methods=["GET", "PATCH", "DELETE"])
@jwt_required()
def manage_collection(id):
    session = SessionLocal()
    user_id = get_jwt_identity()
    
    try:
        collection = session.query(Collection).filter(Collection.id == id, Collection.user_id == user_id).first()
        
        if not collection:
            return jsonify({"error": "Collection not found"}), 404
        
        if request.method == "GET":
            items = session.query(CollectionItem).filter(CollectionItem.collection_id == id).all()
            return jsonify({
                "id": collection.id,
                "name": collection.name,
                "description": collection.description,
                "media_type": collection.media_type,
                "items": [{
                    "id": item.id,
                    "item_id": item.item_id,
                    "note": item.note,
                } for item in items]
            }), 200
        
        if request.method == "PATCH":
            data = request.json
            for key in data:
                if hasattr(collection, key) and key not in ['id', 'user_id']:
                    setattr(collection, key, data[key])
            session.commit()
            return jsonify({"message": "Collection updated successfully"}), 200
        
        if request.method == "DELETE":
            session.delete(collection)
            session.commit()
            return jsonify({"message": "Collection deleted successfully"}), 200
    except SQLAlchemyError:
        session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@api_bp.route("/collections/<id>/items", methods=["POST"])
@jwt_required()
def add_collection_item(id):
    session = SessionLocal()
    user_id = get_jwt_identity()
    
    try:
        # Verify user owns this collection
        collection = session.query(Collection).filter(Collection.id == id, Collection.user_id == user_id).first()
        if not collection:
            return jsonify({"error": "Collection not found"}), 404
        
        data = request.json
        if not data.get('item_id'):
            return jsonify({"error": "item_id is required"}), 400
        
        # Check if item already exists in collection
        existing = session.query(CollectionItem).filter(
            CollectionItem.collection_id == id,
            CollectionItem.item_id == data['item_id']
        ).first()
        
        if existing:
            return jsonify({"error": "Item already in collection"}), 400
        
        new_item = CollectionItem(
            id=str(uuid.uuid4()),
            collection_id=id,
            item_id=data['item_id'],
            note=data.get('note')
        )
        session.add(new_item)
        session.commit()
        return jsonify({"message": "Item added to collection", "id": new_item.id}), 201
    except SQLAlchemyError:
        session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@api_bp.route("/collections/<id>/items/<item_id>", methods=["DELETE"])
@jwt_required()
def remove_collection_item(id, item_id):
    session = SessionLocal()
    user_id = get_jwt_identity()
    
    try:
        # Verify user owns this collection
        collection = session.query(Collection).filter(Collection.id == id, Collection.user_id == user_id).first()
        if not collection:
            return jsonify({"error": "Collection not found"}), 404
        
        item = session.query(CollectionItem).filter(
            CollectionItem.collection_id == id,
            CollectionItem.item_id == item_id
        ).first()
        
        if not item:
            return jsonify({"error": "Item not found in collection"}), 404
        
        session.delete(item)
        session.commit()
        return jsonify({"message": "Item removed from collection"}), 200
    except SQLAlchemyError:
        session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

# -------------------------
# MAGIC SEARCH APIs
# -------------------------
@api_bp.route("/magic-movie-search")
def magic_movie_search():
    query = request.args.get("q")
    if not query:
        return jsonify({"results": []}), 200
    
    try:
        search_res = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params={"query": query, "api_key": Config.TMDB_API_KEY, "language": "en-US"},
            timeout=10
        )
        search_data = search_res.json()
        results = []
        
        for item in search_data.get("results", [])[:5]:
            movie_id = item.get("id")
            details_res = requests.get(
                f"https://api.themoviedb.org/3/movie/{movie_id}",
                params={"api_key": Config.TMDB_API_KEY, "append_to_response": "credits"},
                timeout=5
            )
            details = details_res.json()
            
            director = "Unknown"
            if "credits" in details and "crew" in details["credits"]:
                directors = [crew["name"] for crew in details["credits"]["crew"] if crew["job"] == "Director"]
                if directors:
                    director = directors[0]
            
            results.append({
                "trackName": item.get("title"),
                "artistName": director,
                "releaseDate": item.get("release_date", ""),
                "primaryGenreName": details.get("genres", [{}])[0].get("name", "Film"),
                "artworkUrl100": f"https://image.tmdb.org/t/p/w500{item['poster_path']}" if item.get("poster_path") else "",
                "longDescription": item.get("overview", ""),
                "trackTimeMillis": details.get("runtime", 0) * 60000
            })
        
        return jsonify({"results": results}), 200
    except Exception as e:
        return jsonify({"results": [], "error": "Search failed"}), 500

@api_bp.route("/magic-book-search")
def magic_book_search():
    query = request.args.get("q")
    if not query:
        return jsonify({"items": []}), 200
    
    try:
        res = requests.get(
            "https://www.googleapis.com/books/v1/volumes",
            params={"q": query, "maxResults": 5},
            timeout=10
        )
        return jsonify(res.json()), 200
    except Exception as e:
        return jsonify({"items": [], "error": "Search failed"}), 500

@api_bp.route("/magic-music-search")
def magic_music_search():
    query = request.args.get("q")
    if not query:
        return jsonify({"results": []}), 200
    
    try:
        res = requests.get(
            f"https://itunes.apple.com/search?term={query}&entity=album&limit=5",
            timeout=10
        )
        itunes_data = res.json()
        results = []
        
        for alb in itunes_data.get("results", []):
            artwork = alb.get("artworkUrl100", "")
            if artwork:
                artwork = artwork.replace("100x100", "600x600")
            
            results.append({
                "album_name": alb.get("collectionName"),
                "artist": alb.get("artistName"),
                "artwork": artwork,
                "genre": alb.get("primaryGenreName"),
                "year": alb.get("releaseDate", "")[:4] if alb.get("releaseDate") else "",
                "songs": []
            })
        
        return jsonify({"results": results}), 200
    except Exception as e:
        return jsonify({"results": [], "error": "Search failed"}), 500

@api_bp.route("/magic-podcast-search")
def magic_podcast_search():
    query = request.args.get("q")
    if not query:
        return jsonify({"results": []}), 200
    
    try:
        res = requests.get(
            f"https://itunes.apple.com/search?term={query}&entity=podcast&limit=5",
            timeout=10
        )
        data = res.json()
        results = []
        
        for item in data.get("results", []):
            results.append({
                "title": item.get("collectionName"),
                "host": item.get("artistName"),
                "artwork": item.get("artworkUrl600") or item.get("artworkUrl100"),
                "genre": item.get("primaryGenreName"),
                "episodes": []
            })
        
        return jsonify({"results": results}), 200
    except Exception as e:
        return jsonify({"results": [], "error": "Search failed"}), 500