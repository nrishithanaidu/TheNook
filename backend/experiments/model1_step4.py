# STEP 4: Build user taste profile

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

media = [
    {
        "title": "Pied Piper",
        "genre": "k-pop",
        "moods": ["dark", "obsession", "intense"],
        "rating": 5,
        "status": "finished"
    },
    {
        "title": "Haunting Adeline",
        "genre": "dark romance",
        "moods": ["obsession", "intense"],
        "rating": 5,
        "status": "finished"
    },
    {
        "title": "Gone Girl",
        "genre": "psychological thriller",
        "moods": ["dark", "twisted"],
        "rating": 5,
        "status": "finished"
    },
    {
        "title": "Soft Piano",
        "genre": "instrumental",
        "moods": ["calm", "sad"],
        "rating": 3,
        "status": "finished"
    }
]

# Build ML-readable text
texts = [
    item["genre"] + " " + " ".join(item["moods"])
    for item in media
]

vectorizer = TfidfVectorizer()
vectors = vectorizer.fit_transform(texts)

# Select liked media
liked_indices = [
    i for i, item in enumerate(media)
    if item["rating"] >= 4 and item["status"] == "finished"
]

# Build user taste vector
user_vector = vectors[liked_indices].mean(axis=0)

print("User taste profile created successfully.")
