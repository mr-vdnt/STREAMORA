import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from services.recommendation.shelf_engine import ShelfEngine
from services.recommendation.engines.context_engine import ContextEngine
from services.recommendation.engines.preference_engine import PreferenceEngine

from services.discovery.hero_service import HeroService

class HomeService:
    def __init__(self):
        self.shelf_engine = ShelfEngine()
        self.context_engine = ContextEngine()
        self.preference_engine = PreferenceEngine()
        self.hero_service = HeroService()
        self._cache = {}
        self._cache_ttl = 300 # 5 minutes
        
    def get_home_payload(self, format: str = "all", user_id: int = None) -> dict:
        """
        Assembles the entire homepage layout using the three-stage pipeline.
        Cached to ensure <300ms response time.
        """
        cache_key = f"{format}_{user_id}"
        now = time.time()
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if now - timestamp < self._cache_ttl:
                return cached_data

        current_context = self.context_engine.get_current_context()
        
        # 1. Global Discovery
        payload = self.shelf_engine.generate_home_shelves(user_id=user_id, format=format)
        
        # 2. Context Engine Reordering
        if "sections" in payload:
            payload["sections"] = self.context_engine.reorder_shelves(payload["sections"], current_context)
            
        # 3. Dedicated Hero Selection via HeroService
        with self.shelf_engine.repo.get_session() as session:
            hero = self.hero_service.select_hero(session, format=format, context=current_context)
        # 4. Attach quick-access curated chips and metadata
        payload["genres"] = [
            "Action", "Sci-Fi", "Thrillers", "Comedy", "Family", "Anime", "Documentaries", "Drama", "Crime", "Romance"
        ]
        payload["studios"] = [
            {"id": "marvel", "name": "Marvel Studios", "logo_url": "https://img.icons8.com/color/96/marvel.png"},
            {"id": "dc", "name": "DC Studios", "logo_url": "https://img.icons8.com/color/96/dc-comics.png"},
            {"id": "a24", "name": "A24", "logo_url": "https://img.icons8.com/ios-filled/100/ffffff/a24.png"},
            {"id": "disney", "name": "Walt Disney Pictures", "logo_url": "https://img.icons8.com/color/96/disney-logo.png"},
            {"id": "warner", "name": "Warner Bros", "logo_url": "https://img.icons8.com/color/96/warner-bros.png"}
        ]
        payload["collections"] = [
            {"id": "spiderman", "title": "Spider-Man Universe", "item_count": 8},
            {"id": "mcu", "title": "Marvel Cinematic Universe", "item_count": 32},
            {"id": "nolan", "title": "Christopher Nolan Collection", "item_count": 11},
            {"id": "oscar", "title": "Oscar Best Picture Winners", "item_count": 24}
        ]

        # Extract continue watching items from first shelf if present or mock active user progress
        payload["continue_watching"] = []
        if payload.get("sections") and len(payload["sections"]) > 0:
            first_shelf_items = payload["sections"][0].get("items", [])
            for idx, item in enumerate(first_shelf_items[:3]):
                payload["continue_watching"].append({
                    "content_id": item.get("id"),
                    "title": item.get("title"),
                    "poster_url": item.get("poster_url"),
                    "backdrop_url": item.get("backdrop_url"),
                    "progress_percentage": 45 + (idx * 20),
                    "remaining_mins": 35 - (idx * 10),
                    "season_episode": "S1:E3" if item.get("entity_type") == "tvseries" else None
                })

        self._cache[cache_key] = (payload, now)
        return payload
        
    def get_genre_payload(self, genre: str, user_id: int = None) -> dict:
        """
        Assembles a dedicated genre page layout with dynamic shelves.
        """
        payload = self.shelf_engine.generate_genre_shelves(genre=genre, user_id=user_id)
        current_context = self.context_engine.get_current_context()
        current_context["genre"] = genre
        
        # Dedicated Hero Selection via HeroService
        with self.shelf_engine.repo.get_session() as session:
            hero = self.hero_service.select_hero(session, format="all", context=current_context)
            if hero:
                payload["hero"] = hero
            
        return payload
