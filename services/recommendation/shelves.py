from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from services.repository.catalog_db import Content
from services.recommendation.specifications import (
    Specification,
    MovieOnlySpecification,
    SeriesOnlySpecification,
    TrendingIndiaSpecification,
    GenreSpecification,
    ThemeSpecification,
    MinRatingSpecification,
    MinPopularitySpecification,
    LanguageSpecification
)
from services.recommendation.query_builder import CandidateQueryBuilder
from services.recommendation.pipeline import RecommendationPipeline
import datetime

class ExposureTracker:
    """Tracks content exposure across shelves to eliminate title overlap."""
    def __init__(self):
        self.exposed_ids: set = set()

    def can_show(self, item_id: int) -> bool:
        return item_id not in self.exposed_ids

    def record_exposure(self, item_id: int):
        self.exposed_ids.add(item_id)


class DeclarativeShelf:
    """
    Declarative Shelf definition combining:
    - Unique ID and Display Title
    - Candidate Specification (Query criteria)
    - Target Limit & Format Override
    """
    def __init__(
        self,
        shelf_id: str,
        title: str,
        specification: Specification,
        limit: int = 15,
        target_format: str = "all"
    ):
        self.shelf_id = shelf_id
        self.title = title
        self.specification = specification
        self.limit = limit
        self.target_format = target_format

    def generate(
        self,
        session: Session,
        exposure_tracker: ExposureTracker,
        format_override: str = "all"
    ) -> Dict[str, Any]:
        target_fmt = self.target_format if self.target_format != "all" else format_override
        query_builder = CandidateQueryBuilder(session)

        pipeline = RecommendationPipeline.build_default_7_stage_pipeline()
        
        context = {
            "query_builder": query_builder,
            "specification": self.specification,
            "target_format": target_fmt,
            "exposure_tracker": exposure_tracker,
            "output_limit": self.limit,
            "candidate_limit": 150
        }

        items = pipeline.execute([], context)

        return {
            "id": self.shelf_id,
            "title": self.title,
            "type": "carousel",
            "items": items
        }


class ShelfRegistry:
    """Registry of declarative home and category shelves."""
    @staticmethod
    def get_home_shelves() -> List[DeclarativeShelf]:
        return [
            DeclarativeShelf(
                shelf_id="trending_india",
                title="🇮🇳 Trending in India",
                specification=TrendingIndiaSpecification(min_popularity=30.0),
                limit=15
            ),
            DeclarativeShelf(
                shelf_id="movies_only",
                title="🎬 Blockbuster Movies",
                specification=MovieOnlySpecification() & MinPopularitySpecification(40.0),
                limit=15,
                target_format="movie"
            ),
            DeclarativeShelf(
                shelf_id="series_only",
                title="📺 Bingeable TV Series",
                specification=SeriesOnlySpecification() & MinPopularitySpecification(30.0),
                limit=15,
                target_format="series"
            ),
            DeclarativeShelf(
                shelf_id="mind_bending",
                title="🌀 Mind-Bending & Sci-Fi",
                specification=ThemeSpecification("mind_bending") | GenreSpecification("Sci-Fi"),
                limit=15
            ),
            DeclarativeShelf(
                shelf_id="crime_thriller",
                title="🕵️ Crime & Thrillers",
                specification=GenreSpecification("Crime") | GenreSpecification("Thriller"),
                limit=15
            ),
            DeclarativeShelf(
                shelf_id="top_rated",
                title="⭐ Critically Acclaimed",
                specification=MinRatingSpecification(8.0),
                limit=15
            )
        ]
