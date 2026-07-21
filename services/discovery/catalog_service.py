import os
import sys
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Ensure CatalogRepository can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from services.repository.catalog_db import CatalogRepository

class DiscoveryQuery(BaseModel):
    genre: Optional[str] = None
    year: Optional[int] = None
    language: Optional[str] = None
    type: Optional[str] = None
    sort: Optional[str] = "popularity"  # popularity, rating, year
    page: int = 1
    limit: int = 20

class CatalogService:
    def __init__(self):
        self.repo = CatalogRepository()
        
        # Simple cache for discovery responses
        self._cache = {}
        
        # We can extract the normalization logic directly, but for now we'll implement a robust one
        # to ensure it resolves variations (e.g. "Sci-Fi" -> "Science Fiction")
        self._genre_synonyms = {
            "sci-fi": "Science Fiction",
            "science fiction": "Science Fiction",
            "scifi": "Science Fiction",
            "rom-com": "Romance",
            "romcom": "Romance",
            "romantic comedy": "Romance",
            "action": "Action",
            "adventure": "Adventure",
            "comedy": "Comedy",
            "crime": "Crime",
            "drama": "Drama",
            "fantasy": "Fantasy",
            "horror": "Horror",
            "romance": "Romance",
            "thriller": "Thriller",
            "animation": "Animation",
            "documentary": "Documentary"
        }

    def _normalize_genre(self, genre: str) -> str:
        if not genre:
            return None
        lower_g = genre.strip().lower()
        return self._genre_synonyms.get(lower_g, genre.strip().title())

    def _generate_cache_key(self, query: DiscoveryQuery) -> str:
        return f"{query.genre}_{query.year}_{query.language}_{query.type}_{query.sort}_{query.page}_{query.limit}"

    def discover(self, query: DiscoveryQuery) -> Dict[str, Any]:
        """
        Executes a deterministic discovery query against the movie repository.
        """
        cache_key = self._generate_cache_key(query)
        if cache_key in self._cache:
            return self._cache[cache_key]

        movies_db = self.repo.get_all()
        results = []

        target_genre = self._normalize_genre(query.genre) if query.genre else None
        target_year = str(query.year) if query.year else None
        target_language = query.language.lower() if query.language else None
        target_type = query.type.lower() if query.type else None

        for iid, row in movies_db.items():
            # 1. Filter by Type
            if target_type:
                ctype = str(row.get('content_type', '')).lower()
                if ctype != target_type:
                    continue

            # 2. Filter by Language
            if target_language:
                lang = str(row.get('language', '')).lower()
                if target_language not in lang:
                    continue

            # 3. Filter by Year
            if target_year:
                year = str(row.get('year', ''))
                if target_year != year:
                    continue

            # 4. Filter by Genre
            if target_genre:
                genres = [g.strip() for g in str(row.get('genres', '')).split('|')]
                # exact or normalized match
                if target_genre not in genres:
                    # Let's also check if it's a substring match for robustness
                    matched = False
                    for g in genres:
                        if target_genre.lower() in g.lower():
                            matched = True
                            break
                    if not matched:
                        continue

            results.append(row)

        # 5. Sorting
        if query.sort == "rating":
            results.sort(key=lambda x: float(x.get('rating', 0) or 0), reverse=True)
        elif query.sort == "year":
            results.sort(key=lambda x: str(x.get('year', '0')), reverse=True)
        else: # default popularity
            results.sort(key=lambda x: float(x.get('popularity', 0) or 0), reverse=True)

        # 6. Pagination
        total_items = len(results)
        start_idx = (query.page - 1) * query.limit
        end_idx = start_idx + query.limit
        paginated = results[start_idx:end_idx]

        # 7. Map to response payloads
        mapped_results = []
        for r in paginated:
            mapped_results.append({
                "item_id": int(r.get('item_id', 0)),
                "title": str(r.get('title', '')),
                "poster_url": str(r.get('poster_url', '')),
                "backdrop_url": str(r.get('backdrop_url', '')),
                "overview": str(r.get('overview', '')),
                "rich_metadata": {
                    "title": str(r.get('title', '')),
                    "year": str(r.get('year', '2024')),
                    "rating": float(r.get('rating', 8.0) or 8.0),
                    "runtime": str(r.get('runtime', '120 min')),
                    "director": str(r.get('director', 'Unknown Director')),
                    "genres": str(r.get('genres', '')).split('|'),
                    "themes": str(r.get('themes', '')).split('|'),
                    "content_type": str(r.get('content_type', 'movie'))
                }
            })

        response = {
            "query": query.dict(),
            "total": total_items,
            "page": query.page,
            "results": mapped_results
        }
        
        # Cache for subsequent reads
        self._cache[cache_key] = response
        return response

    def get_categories(self):
        """Returns normalized genres available in the DB."""
        genres = self.repo.get_genres()
        return [{"name": g} for g in genres]
