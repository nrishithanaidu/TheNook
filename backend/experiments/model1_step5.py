# STEP 5: Generate recommendations

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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

# Step 1–2: build text
texts = [
    item["genre"] + " " + " ".join(item["moods"])
    for item in media
]

# Step 3: TF-IDF
vectorizer = TfidfVectorizer()
vectors = vectorizer.fit_transform(texts)

# Step 4: user taste
liked_indices = [
    i for i, item in enumerate(media)
    if item["rating"] >= 4 and item["status"] == "finished"
]

user_vector = np.asarray(vectors[liked_indices].mean(axis=0))

# Step 5: similarity
scores = cosine_similarity(user_vector, vectors)[0]

# Rank results
ranked = sorted(
    zip(media, scores),
    key=lambda x: x[1],
    reverse=True
)

print("\nRecommended media:\n")

for item, score in ranked:
    print(f"{item['title']} → similarity: {round(score, 2)}")
