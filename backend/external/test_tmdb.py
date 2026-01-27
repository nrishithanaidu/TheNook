from tmdb_service import search_movies

movies = search_movies("psychological thriller")

for m in movies:
    print("\nTITLE:", m["title"])
    print("OVERVIEW:", m["overview"][:150], "...")

