from flask import Blueprint, request, jsonify

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    verify_jwt_in_request
)

from flask_jwt_extended.exceptions import NoAuthorizationError

from config import Config

from recommender.service import (
    log_user_emotion,
    get_user_recommendations,
    get_user_emotion_history
)

recommender_bp = Blueprint(
    "recommender",
    __name__,
    url_prefix="/api"
)

# ============================================================
# ✅ Emotion Log Route (Guest + Auth Supported)
# ============================================================

@recommender_bp.route("/emotion/log", methods=["POST"])
def log_emotion():

    user_id = None

    # Try JWT login
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()

    except NoAuthorizationError:
        if not Config.ALLOW_GUEST_RECOMMENDER:
            return jsonify({"error": "Login required"}), 401

        user_id = "guest"

    data = request.json or {}

    media_id = data.get("media_id")
    media_type = data.get("media_type")
    emotion_text = data.get("emotion_text")

    if not media_id or not media_type or not emotion_text:
        return jsonify({"error": "media_id, media_type, emotion_text required"}), 400

    try:
        emotion_vector = log_user_emotion(
            user_id, media_id, media_type, emotion_text
        )

        return jsonify({
            "message": "Emotion logged successfully",
            "emotion_vector": {
                "valence": emotion_vector[0],
                "arousal": emotion_vector[1]
            }
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# ✅ Recommend Route (Guest + Auth Supported)
# ============================================================

@recommender_bp.route("/recommend", methods=["POST"])
def recommend():

    user_id = None

    # Try JWT login
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()

    except NoAuthorizationError:
        if not Config.ALLOW_GUEST_RECOMMENDER:
            return jsonify({"error": "Login required"}), 401

        user_id = "guest"

    data = request.json or {}

    desired_mood = data.get("desired_mood")
    media_type = data.get("media_type")
    limit = data.get("limit", 5)
    mode = data.get("mode", "similar")

    try:
        recommendations = get_user_recommendations(
            user_id=user_id,
            desired_mood=desired_mood,
            media_type=media_type,
            limit=limit,
            mode=mode
        )

        return jsonify({
            "recommendations": recommendations,
            "count": len(recommendations)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# ✅ Auth-Only Routes (Keep Protected)
# ============================================================

@recommender_bp.route("/emotions/me", methods=["GET"])
@jwt_required()
def get_my_emotions():
    user_id = get_jwt_identity()
    emotions = get_user_emotion_history(user_id)
    return jsonify({"emotions": emotions})


@recommender_bp.route("/emotions/stats", methods=["GET"])
@jwt_required()
def get_emotion_stats():
    return jsonify({"message": "Stats route working"})
