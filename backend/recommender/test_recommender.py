# test_recommender.py

from .emotion_parser import parse_emotion
from .emotion_memory import EmotionMemory
from .recommender_engine import EmotionalRecommender


print("\n--- TESTING EMOTION-BASED RECOMMENDER ---\n")

# initialize memory
memory = EmotionMemory()

# -------------------------
# STEP 1: log emotions
# -------------------------

memory.log_emotion("pied_piper_song", parse_emotion("intense and overwhelming"))
memory.log_emotion("pied_piper_song", parse_emotion("dark but powerful"))

memory.log_emotion("dark_romance_book", parse_emotion("sad and emotional"))
memory.log_emotion("dark_romance_book", parse_emotion("heartbroken but intense"))

memory.log_emotion("soft_piano_music", parse_emotion("calm and peaceful"))
memory.log_emotion("soft_piano_music", parse_emotion("relaxed and comforted"))

memory.log_emotion("thriller_movie", parse_emotion("anxious and tense"))
memory.log_emotion("thriller_movie", parse_emotion("overwhelming and stressful"))

print("Emotional profiles learned:")
print(memory.all_media_profiles())

# -------------------------
# STEP 2: recommend
# -------------------------

recommender = EmotionalRecommender(memory)

target_emotion = parse_emotion("I want something intense")

print("\nUser wants something INTENSE\n")

recommendations = recommender.recommend(target_emotion)

for media, distance in recommendations:
    print(f"{media} → distance {round(distance, 3)}")

print("\n--- END TEST ---\n")
