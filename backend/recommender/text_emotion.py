# text_emotion.py

import re
from .emotion_model import EMOTION_KEYWORDS


def extract_emotion_vector(text: str):
    """
    Converts free-text emotion input into (valence, arousal).
    """

    text = text.lower()
    words = re.findall(r"\b\w+\b", text)

    matched = []

    for word in words:
        if word in EMOTION_KEYWORDS:
            matched.append(EMOTION_KEYWORDS[word])

    if not matched:
        # neutral fallback
        return 0.0, 0.5

    avg_valence = sum(v for v, a in matched) / len(matched)
    avg_arousal = sum(a for v, a in matched) / len(matched)

    return round(avg_valence, 3), round(avg_arousal, 3)
