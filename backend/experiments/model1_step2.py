# STEP 2: Convert media into text meaning

media = [
    {
        "title": "Pied Piper",
        "type": "music",
        "genre": "k-pop",
        "moods": ["dark", "obsession", "intense"],
        "rating": 5,
        "status": "finished"
    },
    {
        "title": "Haunting Adeline",
        "type": "book",
        "genre": "dark romance",
        "moods": ["obsession", "intense"],
        "rating": 5,
        "status": "finished"
    },
    {
        "title": "Gone Girl",
        "type": "movie",
        "genre": "psychological thriller",
        "moods": ["dark", "twisted"],
        "rating": 5,
        "status": "finished"
    },
    {
        "title": "Soft Piano",
        "type": "music",
        "genre": "instrumental",
        "moods": ["calm", "sad"],
        "rating": 3,
        "status": "finished"
    }
]

def build_text(media_items):
    texts = []

    for item in media_items:
        text = item["genre"] + " " + " ".join(item["moods"])
        texts.append(text.lower())

    return texts


texts = build_text(media)

print("ML-readable texts:")
for t in texts:
    print("-", t)
