import os
import sys
import time
import threading
from typing import Dict, Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from services.recommendation.shelf_engine import ShelfEngine, HeroSelectionService
from services.recommendation.engines.context_engine import ContextEngine
from services.recommendation.engines.preference_engine import PreferenceEngine

class HomeService:
    def __init__(self):
        self.shelf_engine = ShelfEngine()
        self.context_engine = ContextEngine()
        self.preference_engine = PreferenceEngine()
        self._cache = {}
        self._cache_lock = threading.Lock()
        self._cache_ttl = 300 # 5 minutes
        self._in_flight = {}
        
        threading.Thread(target=self._warm_cache_background, daemon=True).start()

    def _warm_cache_background(self):
        self.get_home_payload(format="all", user_id=32)

    def _refresh_cache(self, cache_key, format, user_id):
        try:
            self._generate_payload(format, user_id, cache_key)
        finally:
            with self._cache_lock:
                if cache_key in self._in_flight:
                    del self._in_flight[cache_key]

    def _generate_payload(self, format, user_id, cache_key=None):
        current_context = self.context_engine.get_current_context()
        
        payload = self.shelf_engine.generate_home_shelves(user_id=user_id, format=format)
        
        if "sections" in payload:
            payload["sections"] = self.context_engine.reorder_shelves(payload["sections"], current_context)
            
        candidates = payload.get("hero_candidates", [])
        top_heroes = HeroSelectionService.select_heroes(candidates, count=5)
        for h in top_heroes:
            if "id" in h and "item_id" not in h:
                h["item_id"] = h["id"]
        
        payload["hero"] = top_heroes[0] if top_heroes else None
        if "hero_candidates" in payload:
            del payload["hero_candidates"]
            
        payload["genres"] = [
            "Action", "Sci-Fi", "Thrillers", "Comedy", "Family", "Anime", "Documentaries", "Drama", "Crime", "Romance"
        ]
        payload["studios"] = [
            {"id": "marvel", "name": "Marvel Studios", "logo_url": "https://img.icons8.com/color/96/marvel.png"},
            {"id": "dc", "name": "DC Studios", "logo_url": "https://img.icons8.com/color/96/dc-comics.png"}
        ]
        payload["collections"] = [
            {"id": "spiderman", "title": "Spider-Man Universe", "item_count": 8},
            {"id": "mcu", "title": "Marvel Cinematic Universe", "item_count": 32}
        ]

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

        now = time.time()
        if cache_key:
            with self._cache_lock:
                self._cache[cache_key] = (payload, now)
        return payload

    def get_home_payload(self, format: str = "all", user_id: int = None) -> dict:
        cache_key = f"{format}_{user_id}"
        now = time.time()
        
        with self._cache_lock:
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if now - timestamp < self._cache_ttl:
                    return cached_data
                else:
                    if cache_key not in self._in_flight:
                        self._in_flight[cache_key] = True
                        threading.Thread(target=self._refresh_cache, args=(cache_key, format, user_id)).start()
                    return cached_data

        with self._cache_lock:
            self._in_flight[cache_key] = True
            
        payload = self._generate_payload(format, user_id, cache_key)
        
        with self._cache_lock:
            if cache_key in self._in_flight:
                del self._in_flight[cache_key]
                
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
