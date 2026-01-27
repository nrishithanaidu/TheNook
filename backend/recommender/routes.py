from flask import Blueprint, request, jsonify
from recommender.service import (
    log_user_emotion,
    get_user_recommendations
)

recommender_bp = Blueprint(
    "recommender",
    __name__,
    url_prefix=""
)


@recommender_bp.route("/api/emotion/log", methods=["POST"])
def log_emotion():
    data = request.json

    user_id = data.get("user_id")
    media_id = data.get("media_id")
    emotion_text = data.get("emotion_text")

    if not all([user_id, media_id, emotion_text]):
        return jsonify({"error": "Missing fields"}), 400

    log_user_emotion(user_id, media_id, emotion_text)

    return jsonify({"message": "Emotion logged successfully"}), 200


@recommender_bp.route("/api/recommend", methods=["POST"])
def recommend():
    data = request.json

    user_id = data.get("user_id")
    desired_mood = data.get("desired_mood")

    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    recommendations = get_user_recommendations(
        user_id=user_id,
        desired_mood=desired_mood
    )

    return jsonify({"recommendations": recommendations})
