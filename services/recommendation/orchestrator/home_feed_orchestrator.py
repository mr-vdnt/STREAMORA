from __future__ import annotations
import time
import asyncio
from typing import List
from services.repository.catalog_db import CatalogRepository
from services.recommendation.recommendation_pipeline import RecommendationPipeline
from services.recommendation.dtos import HomeFeedDTO, ShelfDTO

class HomeFeedOrchestrator:
    """
    Layer 13 Home Feed Orchestrator.
    Assembles a complete multi-shelf personalized home experience in a single optimized request:
    - Continue Watching
    - Top Picks for You (Personalized Home)
    - Trending Across Streamora
    - New Releases
    - Mind-Bending Thrillers (Mood Shelf)
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()
        self.pipeline = RecommendationPipeline(self.repo)

    async def build_home_feed(self, user_id: str) -> HomeFeedDTO:
        start_time = time.time()

        slates_to_build = [
            "continue_watching",
            "personalized_home",
            "trending_for_you",
            "new_releases"
        ]

        tasks = [
            self.pipeline.generate_slate(user_id=user_id, slate_type=s, limit=10)
            for s in slates_to_build
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        shelves: List[ShelfDTO] = []
        for r in results:
            if isinstance(r, ShelfDTO) and r.items:
                shelves.append(r)

        elapsed_ms = (time.time() - start_time) * 1000.0

        return HomeFeedDTO(
            user_id=user_id,
            shelves=shelves,
            latency_ms=round(elapsed_ms, 2)
        )
