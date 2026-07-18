import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from services.discovery.catalog_service import CatalogService, DiscoveryQuery
from services.security.user_data import get_history
from services.repository.movie_repository import MovieRepository

class HomeService:
    def __init__(self):
        self.catalog = CatalogService()
        self.repo = MovieRepository()
        self.executor = ThreadPoolExecutor(max_workers=10)
        self._cache = {}
        self.CACHE_TTL = 1800  # 30 minutes
        
        # Define the structural layout for different formats
        self.layouts = {
            "all": [
                {"id": "trending", "title": "Trending Now", "query": DiscoveryQuery(sort="popularity", limit=15)},
                {"id": "top_picks", "title": "Top Picks For You", "query": DiscoveryQuery(sort="rating", limit=15)},
                {"id": "action", "title": "Action Blockbusters", "query": DiscoveryQuery(genre="Action", limit=15)},
                {"id": "comedy", "title": "Comedy Classics", "query": DiscoveryQuery(genre="Comedy", limit=15)},
                {"id": "scifi", "title": "Mind-Bending Sci-Fi", "query": DiscoveryQuery(genre="Science Fiction", limit=15)},
                {"id": "drama", "title": "Dramatic Masterpieces", "query": DiscoveryQuery(genre="Drama", limit=15)},
                {"id": "anime", "title": "Top Anime", "query": DiscoveryQuery(genre="Animation", limit=15)}
            ],
            "movie": [
                {"id": "trending_movies", "title": "Trending Movies", "query": DiscoveryQuery(type="movie", sort="popularity", limit=15)},
                {"id": "top_movies", "title": "Top Rated Movies", "query": DiscoveryQuery(type="movie", sort="rating", limit=15)},
                {"id": "action_movies", "title": "Action Movies", "query": DiscoveryQuery(type="movie", genre="Action", limit=15)},
                {"id": "comedy_movies", "title": "Comedy Movies", "query": DiscoveryQuery(type="movie", genre="Comedy", limit=15)},
                {"id": "scifi_movies", "title": "Sci-Fi Movies", "query": DiscoveryQuery(type="movie", genre="Science Fiction", limit=15)},
                {"id": "drama_movies", "title": "Drama Movies", "query": DiscoveryQuery(type="movie", genre="Drama", limit=15)},
                {"id": "horror_movies", "title": "Horror Movies", "query": DiscoveryQuery(type="movie", genre="Horror", limit=15)},
                {"id": "thriller_movies", "title": "Thriller Movies", "query": DiscoveryQuery(type="movie", genre="Thriller", limit=15)},
                {"id": "anime_movies", "title": "Animation Movies", "query": DiscoveryQuery(type="movie", genre="Animation", limit=15)}
            ],
            "series": [
                {"id": "trending_series", "title": "Trending Series", "query": DiscoveryQuery(type="series", sort="popularity", limit=15)},
                {"id": "top_series", "title": "Top Rated Series", "query": DiscoveryQuery(type="series", sort="rating", limit=15)},
                {"id": "action_series", "title": "Action Series", "query": DiscoveryQuery(type="series", genre="Action", limit=15)},
                {"id": "comedy_series", "title": "Comedy Series", "query": DiscoveryQuery(type="series", genre="Comedy", limit=15)},
                {"id": "drama_series", "title": "Drama Series", "query": DiscoveryQuery(type="series", genre="Drama", limit=15)},
                {"id": "scifi_series", "title": "Sci-Fi Series", "query": DiscoveryQuery(type="series", genre="Science Fiction", limit=15)},
                {"id": "anime_series", "title": "Anime Series", "query": DiscoveryQuery(type="anime", limit=15)}
            ]
        }
        
    def _fetch_section(self, section_def: dict) -> dict:
        """Executes a single catalog fetch."""
        cache_key = f"{section_def['id']}_{hash(str(section_def['query'].dict()))}"
        
        # Check cache
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if time.time() - entry['timestamp'] < self.CACHE_TTL:
                return entry['data']
                
        try:
            results = self.catalog.discover(section_def["query"])
            data = {
                "id": section_def["id"],
                "title": section_def["title"],
                "items": results.get("results", [])
            }
            # Save to cache
            self._cache[cache_key] = {
                'timestamp': time.time(),
                'data': data
            }
            return data
        except Exception as e:
            print(f"Error fetching section {section_def['id']}: {e}")
            return {
                "id": section_def["id"],
                "title": section_def["title"],
                "items": []
            }

    def _get_continue_watching(self, user_id: int, format: str) -> dict:
        """Retrieves user's watch history mapped to movie payloads."""
        if not user_id or user_id == 32: # 32 is the anonymous default in main.py
            return None
            
        history = get_history(user_id)
        if not history:
            return None
            
        # Filter history by format
        filtered = []
        target_type = "movie" if format == "movie" else ("series" if format == "series" else None)
        
        for h in history:
            iid = h.get("item_id") if isinstance(h, dict) else h
            row = self.repo.get_by_id(iid)
            if row:
                ctype = row.get("content_type", "movie")
                if target_type and ctype != target_type and not (target_type == "series" and ctype == "anime"):
                    continue
                    
                filtered.append({
                    "item_id": int(row.get('item_id', 0)),
                    "title": str(row.get('title', '')),
                    "poster_url": str(row.get('poster_url', '')),
                    "backdrop_url": str(row.get('backdrop_url', '')),
                    "overview": str(row.get('overview', '')),
                    "rich_metadata": {
                        "title": str(row.get('title', '')),
                        "year": str(row.get('year', '2024')),
                        "rating": float(row.get('rating', 8.0) or 8.0),
                        "runtime": str(row.get('runtime', '120 min')),
                        "director": str(row.get('director', 'Unknown Director')),
                        "genres": str(row.get('genres', '')).split('|'),
                        "themes": str(row.get('themes', '')).split('|'),
                        "content_type": str(row.get('content_type', 'movie'))
                    }
                })
                
        if not filtered:
            return None
            
        return {
            "id": "continue_watching",
            "title": "Continue Watching",
            "items": filtered[:15]
        }

    def get_home_payload(self, format: str = "all", user_id: int = None) -> Dict[str, Any]:
        """
        Assembles the entire homepage layout in a single concurrent pass.
        """
        layout = self.layouts.get(format, self.layouts["all"])
        
        # Execute sections in parallel
        futures = []
        for sec in layout:
            futures.append(self.executor.submit(self._fetch_section, sec))
            
        sections = []
        
        # 1. Add personalized section (fast local execution)
        continue_watching = self._get_continue_watching(user_id, format)
        if continue_watching:
            sections.append(continue_watching)
            
        # 2. Add static parallelized sections
        for future in futures:
            sec_data = future.result()
            if sec_data and sec_data.get("items"):
                sections.append(sec_data)
                
        # 3. Determine Hero item (usually the top trending item)
        hero = {}
        if sections and len(sections[-1]["items"]) > 0: # Grab from the first resolved section just in case, trending is best
            for sec in sections:
                if sec["id"].startswith("trending") and sec["items"]:
                    hero = sec["items"][0]
                    break
            if not hero:
                hero = sections[0]["items"][0]

        return {
            "hero": hero,
            "sections": sections
        }
