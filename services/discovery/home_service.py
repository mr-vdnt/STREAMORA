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

class HomeService:
    def __init__(self):
        self.shelf_engine = ShelfEngine()
        self.context_engine = ContextEngine()
        self.preference_engine = PreferenceEngine()
        self._cache = {}
        self._cache_ttl = 300 # 5 minutes
        
    def get_home_payload(self, format: str = "all", user_id: int = None) -> dict:
        """
        Assembles the entire homepage layout using the three-stage pipeline.
        Cached to ensure <300ms response time.
        """
        cache_key = f"{format}_{user_id}"
        current_context = self.context_engine.get_current_context()
        
        if cache_key in self._cache:
            entry, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                payload = entry.copy()
                if "top_heroes" in payload and payload["top_heroes"]:
                    payload["hero"] = self.context_engine.select_hero(payload["top_heroes"], current_context)
                return payload
                
        # 1. Global Discovery
        payload = self.shelf_engine.generate_home_shelves(user_id=user_id, format=format)
        
        # 2. Personalization
        # user_prefs = self.preference_engine.get_user_preferences(user_id)
        # TODO: Filter or re-rank shelves based on user_prefs
        
        # 3. Context Engine
        if "sections" in payload:
            payload["sections"] = self.context_engine.reorder_shelves(payload["sections"], current_context)
            
        self._cache[cache_key] = (payload, time.time())
        
        # Assign dynamic hero before returning
        ret_payload = payload.copy()
        if "top_heroes" in ret_payload and ret_payload["top_heroes"]:
            ret_payload["hero"] = self.context_engine.select_hero(ret_payload["top_heroes"], current_context)
            
        return ret_payload
        
    def get_genre_payload(self, genre: str, user_id: int = None) -> dict:
        """
        Assembles a dedicated genre page layout with dynamic shelves.
        """
        payload = self.shelf_engine.generate_genre_shelves(genre=genre, user_id=user_id)
        current_context = self.context_engine.get_current_context()
        
        # Assign dynamic hero before returning
        if "top_heroes" in payload and payload["top_heroes"]:
            payload["hero"] = self.context_engine.select_hero(payload["top_heroes"], current_context)
            
        return payload
