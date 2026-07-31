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

    def generate_home_shelves(self, user_id: int = None, format: str = "all") -> Dict[str, Any]:
        exposure = ExposureTracker()
        shelves = []
        hero_candidates = []

        with self.repo.get_session() as session:
            home_shelves = ShelfRegistry.get_home_shelves()
            for shelf_def in home_shelves:
                shelf_data = shelf_def.generate(session, exposure, format_override=format)
                if shelf_data["items"]:
                    shelves.append(shelf_data)
                    hero_candidates.extend(shelf_data["items"])

            top_heroes = HeroSelectionService.select_heroes(hero_candidates, count=5)

        return {
            "top_heroes": top_heroes,
            "sections": shelves
        }

    def generate_genre_shelves(self, genre: str, user_id: int = None) -> Dict[str, Any]:
        exposure = ExposureTracker()
        
        genre_shelves = [
            DeclarativeShelf("trending_genre", f"🔥 Trending {genre.title()}", GenreSpecification(genre) & MinPopularitySpecification(30.0), limit=15),
            DeclarativeShelf("top_genre", f"⭐ Top Rated {genre.title()}", GenreSpecification(genre) & MinRatingSpecification(7.5), limit=15),
        ]

        shelves = []
        hero_candidates = []

        with self.repo.get_session() as session:
            for shelf_def in genre_shelves:
                shelf_data = shelf_def.generate(session, exposure)
                if shelf_data["items"]:
                    shelves.append(shelf_data)
                    hero_candidates.extend(shelf_data["items"])

            top_heroes = HeroSelectionService.select_heroes(hero_candidates, count=5)

        return {
            "top_heroes": top_heroes,
            "sections": shelves
        }
