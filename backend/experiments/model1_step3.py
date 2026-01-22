# STEP 3: Convert text into vectors using TF-IDF

from sklearn.feature_extraction.text import TfidfVectorizer

texts = [
    "k-pop dark obsession intense",
    "dark romance obsession intense",
    "psychological thriller dark twisted",
    "instrumental calm sad"
]

vectorizer = TfidfVectorizer()
vectors = vectorizer.fit_transform(texts)

print("TF-IDF matrix shape:", vectors.shape)

print("\nVocabulary:")
print(vectorizer.get_feature_names_out())
