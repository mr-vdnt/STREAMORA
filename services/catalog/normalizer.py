from typing import Dict, Any, List

class MetadataNormalizer:
    """
    Standardizes external raw payloads (TMDB, IMDb, Watchmode) into canonical catalog schema dictionaries.
    """

    @staticmethod
    def normalize_movie(raw: Dict[str, Any]) -> Dict[str, Any]:
        genres = raw.get("genres", [])
        genre_str = "|".join([g["name"] if isinstance(g, dict) else str(g) for g in genres]) if isinstance(genres, list) else str(genres)

        return {
            "tmdb_id": raw.get("id") or raw.get("tmdb_id"),
            "imdb_id": raw.get("imdb_id"),
            "title": raw.get("title") or raw.get("name") or "Untitled",
            "original_title": raw.get("original_title") or raw.get("title"),
            "overview": raw.get("overview", ""),
            "release_date": raw.get("release_date", ""),
            "year": str(raw.get("release_date", ""))[:4] if raw.get("release_date") else str(raw.get("year", "2024")),
            "genres": genre_str,
            "themes": str(raw.get("themes", "")),
            "poster_url": raw.get("poster_path") or raw.get("poster_url", ""),
            "backdrop_url": raw.get("backdrop_path") or raw.get("backdrop_url", ""),
            "rating": float(raw.get("vote_average") or raw.get("rating") or 0.0),
            "popularity": float(raw.get("popularity", 0.0)),
            "language": raw.get("original_language") or raw.get("language") or "en",
            "runtime": int(raw.get("runtime") or 120),
            "tagline": raw.get("tagline", ""),
            "director": raw.get("director", "Unknown"),
            "cast": raw.get("cast", ""),
            "entity_type": "movie"
        }

    @staticmethod
    def normalize_series(raw: Dict[str, Any]) -> Dict[str, Any]:
        genres = raw.get("genres", [])
        genre_str = "|".join([g["name"] if isinstance(g, dict) else str(g) for g in genres]) if isinstance(genres, list) else str(genres)

        return {
            "tmdb_id": raw.get("id") or raw.get("tmdb_id"),
            "imdb_id": raw.get("imdb_id"),
            "title": raw.get("name") or raw.get("title") or "Untitled Series",
            "original_title": raw.get("original_name") or raw.get("title"),
            "overview": raw.get("overview", ""),
            "release_date": raw.get("first_air_date", ""),
            "year": str(raw.get("first_air_date", ""))[:4] if raw.get("first_air_date") else str(raw.get("year", "2024")),
            "genres": genre_str,
            "themes": str(raw.get("themes", "")),
            "poster_url": raw.get("poster_path") or raw.get("poster_url", ""),
            "backdrop_url": raw.get("backdrop_path") or raw.get("backdrop_url", ""),
            "rating": float(raw.get("vote_average") or raw.get("rating") or 0.0),
            "popularity": float(raw.get("popularity", 0.0)),
            "language": raw.get("original_language") or raw.get("language") or "en",
            "total_seasons": int(raw.get("number_of_seasons") or raw.get("total_seasons") or 1),
            "total_episodes": int(raw.get("number_of_episodes") or raw.get("total_episodes") or 10),
            "in_production": bool(raw.get("in_production", False)),
            "creator": raw.get("creator", "Unknown"),
            "cast": raw.get("cast", ""),
            "entity_type": "tvseries"
        }
