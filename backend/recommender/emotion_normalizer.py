# emotion_normalizer.py

from .emotion_model import EMOTION_KEYWORDS

# Maps varied emotional expressions → core emotion keywords

EMOTION_SYNONYMS = {

    # SADNESS
    "melancholic": "sad",
    "heartbroken": "sad",
    "sorrowful": "sad",
    "grieving": "sad",
    "tearful": "sad",
    "aching": "sad",
    "heavy": "sad",
    "down": "sad",

    # HAPPINESS
    "joyful": "happy",
    "elated": "happy",
    "delighted": "happy",
    "thrilled": "happy",
    "euphoric": "happy",
    "content": "happy",
    "pleased": "happy",

    # CALM / PEACE
    "serene": "calm",
    "tranquil": "calm",
    "peaceful": "calm",
    "grounded": "calm",
    "soothed": "calm",
    "gentle": "calm",
    "relaxed": "calm",

    # INTENSITY
    "overwhelming": "intense",
    "consuming": "intense",
    "powerful": "intense",
    "explosive": "intense",
    "fierce": "intense",
    "passionate": "intense",

    # ANXIETY
    "nervous": "anxious",
    "uneasy": "anxious",
    "panicked": "anxious",
    "restless": "anxious",
    "worried": "anxious",

    # NUMBNESS
    "hollow": "numb",
    "blank": "numb",
    "detached": "numb",
    "emotionless": "numb",
    "void": "numb",
}



def normalize_word(word: str):
    """
    Converts synonym to base emotion keyword if possible.
    """

    if word in EMOTION_KEYWORDS:
        return word

    if word in EMOTION_SYNONYMS:
        return EMOTION_SYNONYMS[word]

    return None
