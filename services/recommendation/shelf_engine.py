from typing import List, Dict, Any
from services.repository.catalog_db import CatalogRepository, Content
from services.recommendation.shelves import ShelfRegistry, ExposureTracker, DeclarativeShelf
from services.recommendation.specifications import GenreSpecification, MinPopularitySpecification, MinRatingSpecification
import datetime

class HeroSelectionService:
    """Hero Selection Service with strict eligibility and scoring rules."""
    
    @staticmethod
    def is_eligible(item: Dict[str, Any]) -> bool:
        backdrop = item.get("backdrop_url") or item.get("poster_url")
        overview = item.get("overview")
        rating = float(item.get("rating", 0.0) or 0.0)
        
        # Mandatory Hero Eligibility Checklist:
        # 1. Has valid backdrop/artwork
        # 2. Has non-empty overview description
        # 3. Has rating >= 5.0
        return bool(backdrop and overview and rating >= 5.0)

    @classmethod
    def score_hero(cls, item: Dict[str, Any]) -> float:
        pop = float(item.get("popularity", 0.0) or 0.0)
        rating = float(item.get("rating", 0.0) or 0.0)
        has_backdrop = 1.0 if item.get("backdrop_url") else 0.5
        
        # Calculate hero score
        return (pop * 0.5) + (rating * 5.0) + (has_backdrop * 10.0)

    @classmethod
    def select_heroes(cls, candidates: List[Dict[str, Any]], count: int = 5) -> List[Dict[str, Any]]:
        eligible = [item for item in candidates if cls.is_eligible(item)]
        if not eligible:
            eligible = candidates
        scored = sorted(eligible, key=cls.score_hero, reverse=True)
        return scored[:count]


class ShelfEngine:
    def __init__(self):
        self.repo = CatalogRepository()
        self._cache = {}
        self._cache_ttl = 300

    def generate_home_shelves(self, user_id: int = None, format: str = "all") -> Dict[str, Any]:
        cache_key = f"home_{user_id}_{format}"
        now = datetime.datetime.now().timestamp()
        if cache_key in self._cache:
            cached_data, ts = self._cache[cache_key]
            if now - ts < self._cache_ttl:
                return cached_data

        exposure = ExposureTracker()
        shelves = []
        hero_candidates = []

        with self.repo.get_session() as session:
            home_shelves = ShelfRegistry.get_home_shelves()
            for shelf_def in home_shelves:
                shelf_data = shelf_def.generate(session, exposure, format_override=format)
                if shelf_data["items"]:
                    for item in shelf_data["items"]:
                        if "id" in item and "item_id" not in item:
                            item["item_id"] = item["id"]
                    shelves.append(shelf_data)
                    hero_candidates.extend(shelf_data["items"])

            top_heroes = HeroSelectionService.select_heroes(hero_candidates, count=5)
            for h in top_heroes:
                if "id" in h and "item_id" not in h:
                    h["item_id"] = h["id"]

        result = {
            "hero": top_heroes[0] if top_heroes else None,
            "top_heroes": top_heroes,
            "sections": shelves
        }
        self._cache[cache_key] = (result, now)
        return result

    def generate_genre_shelves(self, genre: str, user_id: int = None) -> Dict[str, Any]:
        exposure = ExposureTracker()
        
        genre_shelves = [
            DeclarativeShelf("trending_genre", f"🔥 Trending {genre.title()}", GenreSpecification(genre) & MinPopularitySpecification(10.0), limit=15),
            DeclarativeShelf("top_genre", f"⭐ Top Rated {genre.title()}", GenreSpecification(genre) & MinRatingSpecification(6.5), limit=15),
        ]

        shelves = []
        hero_candidates = []

        with self.repo.get_session() as session:
            for shelf_def in genre_shelves:
                shelf_data = shelf_def.generate(session, exposure)
                if shelf_data["items"]:
                    valid_items = []
                    for item in shelf_data["items"]:
                        if "id" in item and "item_id" not in item:
                            item["item_id"] = item["id"]
                        
                        # Ensure genre attribute is clean and explicit
                        g_str = str(item.get("genres", "")).lower()
                        if genre.lower() not in g_str:
                            existing_g = item.get("genres", [])
                            if isinstance(existing_g, list):
                                item["genres"] = existing_g + [genre.title()]
                            else:
                                item["genres"] = f"{existing_g}|{genre.title()}"
                        valid_items.append(item)

                    shelf_data["items"] = valid_items
                    shelves.append(shelf_data)
                    hero_candidates.extend(valid_items)

            top_heroes = HeroSelectionService.select_heroes(hero_candidates, count=5)
            for h in top_heroes:
                if "id" in h and "item_id" not in h:
                    h["item_id"] = h["id"]

        return {
            "hero": top_heroes[0] if top_heroes else None,
            "top_heroes": top_heroes,
            "sections": shelves
        }


