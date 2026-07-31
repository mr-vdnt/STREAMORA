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
            if hero:
                payload["hero"] = hero

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
