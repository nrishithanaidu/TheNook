from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import Base, engine
from routes import api_bp
from recommender.routes import recommender_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
        # ✅ Create all tables automatically
    Base.metadata.create_all(bind=engine)

    # Initialize CORS with proper configuration
    CORS(app, resources={
        r"/api/*": {
            "origins": Config.CORS_ORIGINS,
            "methods": ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Initialize JWT
    jwt = JWTManager(app)
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            "error": "Token has expired",
            "message": "Please log in again"
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            "error": "Invalid token",
            "message": "Signature verification failed"
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            "error": "Authorization required",
            "message": "Request does not contain an access token"
        }), 401
    
    # Register Blueprints
    # This prefixes all routes in routes.py with /api
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(recommender_bp)

    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({"status": "healthy", "message": "API is running"}), 200
    
    # Root endpoint
    @app.route('/')
    def index():
        return jsonify({
            "message": "Media Tracker API",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "api": "/api",
                "auth": {
                    "register": "/api/auth/register",
                    "login": "/api/auth/login",
                    "me": "/api/auth/me"
                }
            }
        }), 200
    
    # Global error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Endpoint not found"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad request"}), 400
    
    # Create Database Tables in Supabase
    # Only creates if they don't exist
    try:
        Base.metadata.create_all(engine)
        print("✓ Database tables created/verified successfully")
    except Exception as e:
        print(f"✗ Error creating database tables: {e}")
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(
        debug=Config.DEBUG,
        port=5000,
        host='0.0.0.0'  # Allow external connections
    )