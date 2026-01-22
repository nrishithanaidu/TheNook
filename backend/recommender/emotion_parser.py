# emotion_parser.py

import re
from .emotion_model import EMOTION_KEYWORDS
from .emotion_normalizer import normalize_word


def parse_emotion(text: str):
    """
    Converts user-written emotional text into
    a final (valence, arousal) emotional vector.
    """

    text = text.lower()
    words = re.findall(r"\b\w+\b", text)

    emotions = []

    for word in words:
        normalized = normalize_word(word)

        if normalized and normalized in EMOTION_KEYWORDS:
            emotions.append(EMOTION_KEYWORDS[normalized])

    if not emotions:
        # neutral emotional fallback
        return 0.0, 0.5

    avg_valence = sum(v for v, a in emotions) / len(emotions)
    avg_arousal = sum(a for v, a in emotions) / len(emotions)

    return round(avg_valence, 3), round(avg_arousal, 3)
