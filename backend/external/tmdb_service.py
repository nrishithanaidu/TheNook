
import requests
import os

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

BASE_URL = "https://api.themoviedb.org/3"


def search_movies(query, limit=5):
    """
    Search movies from TMDB and return clean metadata
    """
    url = f"{BASE_URL}/search/movie"

    params = {
        "api_key": TMDB_API_KEY,
        "query": query,
        "language": "en-US",
        "page": 1,
        "include_adult": True
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return []

    results = response.json().get("results", [])[:limit]

    movies = []

    for movie in results:
        movies.append({
            "id": movie.get("id"),
            "title": movie.get("title"),
            "overview": movie.get("overview", ""),
            "rating": movie.get("vote_average"),
            "release_date": movie.get("release_date")
        })

    return movies
