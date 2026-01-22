# emotion_model.py

# Valence: -1 (very negative) → +1 (very positive)
# Arousal:  0 (low energy) → 1 (high energy)

EMOTION_KEYWORDS = {
    "empty": (-0.7, 0.2),
    "sad": (-0.6, 0.3),
    "lonely": (-0.6, 0.3),
    "hurt": (-0.7, 0.4),

    "calm": (0.1, 0.2),
    "peaceful": (0.2, 0.2),
    "soft": (0.3, 0.2),
    "comforted": (0.4, 0.3),

    "intense": (-0.4, 0.9),
    "obsessed": (-0.5, 0.8),
    "overwhelming": (-0.6, 0.9),

    "happy": (0.8, 0.8),
    "excited": (0.9, 0.9),

    "anxious": (-0.6, 0.8),
    "tense": (-0.5, 0.7),

    "numb": (-0.4, 0.1),
}
