import os
import sys
import time
import threading
from typing import Dict, Any, Optional

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
        self._cache_ttl = 300  # 5 minutes
        self._in_flight = set()
        self._cold_start_payload = None

        # Precompute cold-start payload asynchronously on boot
        threading.Thread(target=self._init_cold_start, daemon=True).start()

    def _init_cold_start(self):
        """Generates a default cold-start payload to serve instantly on cold cache misses."""
        try:
            payload = self._generate_payload(format="all", user_id=None)
            with self._cache_lock:
                self._cold_start_payload = payload
                self._cache["guest_all"] = (payload, time.time())
        except Exception as e:
            print(f"[HomeService] Cold-start initialization warning: {e}")

    def _refresh_cache(self, cache_key: str, format: str, user_id: Optional[int]):
        try:
            payload = self._generate_payload(format, user_id, cache_key)
            with self._cache_lock:
                self._cache[cache_key] = (payload, time.time())
                if self._cold_start_payload is None and format == "all":
                    self._cold_start_payload = payload
        except Exception as e:
            print(f"[HomeService] Background cache refresh error for {cache_key}: {e}")
        finally:
            with self._cache_lock:
                self._in_flight.discard(cache_key)

    def _generate_payload(self, format: str, user_id: Optional[int], cache_key: Optional[str] = None) -> dict:
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
            "Action & Adventure", "Anime", "Children & Family Movies", "Classic Movies",
            "Comedies", "Documentaries", "Dramas", "Horror Movies", "Independent Movies",
            "International Movies", "Music", "Romantic Movies", "Sci-Fi & Fantasy",
            "Sports Movies", "Thrillers", "TV Shows"
        ]

        payload["continue_watching"] = []
        if payload.get("sections") and len(payload["sections"]) > 0:
            first_shelf_items = payload["sections"][0].get("items", [])
            for idx, item in enumerate(first_shelf_items[:3]):
                payload["continue_watching"].append({
                    "content_id": item.get("id") or item.get("item_id"),
                    "title": item.get("title"),
                    "poster_url": item.get("poster_url"),
                    "backdrop_url": item.get("backdrop_url"),
                    "progress_percentage": 45 + (idx * 20),
                    "remaining_mins": 35 - (idx * 10),
                    "season_episode": "S1:E3" if item.get("entity_type") == "tvseries" else None
                })

        return payload

    def get_home_payload(self, format: str = "all", user_id: Optional[int] = None) -> dict:
        """
        Guaranteed non-blocking Home payload delivery.
        Always returns in <50ms. Never executes shelf generation on caller thread.
        """
        if user_id is None:
            cache_key = f"guest_{format}"
        else:
            cache_key = f"user_{user_id}_{format}"

        now = time.time()
        
        with self._cache_lock:
            # HIT PATH
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                # If expired, trigger non-blocking background refresh
                if now - timestamp >= self._cache_ttl:
                    if cache_key not in self._in_flight:
                        self._in_flight.add(cache_key)
                        threading.Thread(target=self._refresh_cache, args=(cache_key, format, user_id), daemon=True).start()
                return cached_data

            # MISS PATH — Return cold-start payload instantly, generate in background
            fallback = self._cold_start_payload or {
                "hero": None,
                "sections": [],
                "continue_watching": [],
                "genres": [
                    "Action & Adventure", "Anime", "Children & Family Movies", "Classic Movies",
                    "Comedies", "Documentaries", "Dramas", "Horror Movies", "Independent Movies",
                    "International Movies", "Music", "Romantic Movies", "Sci-Fi & Fantasy",
                    "Sports Movies", "Thrillers", "TV Shows"
                ]
            }
            # Cache fallback temporarily so subsequent calls are immediate
            self._cache[cache_key] = (fallback, now)
            
            if cache_key not in self._in_flight:
                self._in_flight.add(cache_key)
                threading.Thread(target=self._refresh_cache, args=(cache_key, format, user_id), daemon=True).start()

            return fallback

    def get_genre_payload(self, genre: str, user_id: Optional[int] = None) -> dict:
        """
        Assembles a dedicated genre page layout with dynamic shelves.
        """
        payload = self.shelf_engine.generate_genre_shelves(genre=genre, user_id=user_id)
        current_context = self.context_engine.get_current_context()
        current_context["genre"] = genre
        
        with self.shelf_engine.repo.get_session() as session:
            hero = self.hero_service.select_hero(session, format="all", context=current_context)
            if hero:
                payload["hero"] = hero
            
        return payload
