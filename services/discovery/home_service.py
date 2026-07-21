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
        
    def get_home_payload(self, format: str = "all", user_id: int = None) -> dict:
        """
        Assembles the entire homepage layout using the three-stage pipeline:
        1. Global Discovery
        2. Personalization
        3. Context Engine
        """
        # 1. Global Discovery
        payload = self.shelf_engine.generate_home_shelves(user_id=user_id, format=format)
        
        # 2. Personalization
        # user_prefs = self.preference_engine.get_user_preferences(user_id)
        # TODO: Filter or re-rank shelves based on user_prefs
        
        # 3. Context Engine
        current_context = self.context_engine.get_current_context()
        if "sections" in payload:
            payload["sections"] = self.context_engine.reorder_shelves(payload["sections"], current_context)
            
        return payload

