from __future__ import annotations
import time
import logging
from typing import Dict, List, Optional, Any
from services.recommendation.recommendation_pipeline import RecommendationPipeline

logger = logging.getLogger("streamora.recommendation.precomputation")

class PrecomputationWorker:
    """
    Background Precomputation Worker for Home Feed Recommendation Snapshots.
    Precomputes user-specific home feed slates asynchronously so GET /api/v3/home is a pure <15ms read operation.
    """

    def __init__(self, pipeline: Optional[RecommendationPipeline] = None):
        self.pipeline = pipeline or RecommendationPipeline()
        self._snapshots: Dict[str, Dict[str, Any]] = {}

    def precompute_user_home_slate(self, user_id: str) -> Dict[str, Any]:
        start_time = time.time()
        shelves = self.pipeline.generate_contextual_shelves(content_id=1, user_id=user_id)
        duration_ms = (time.time() - start_time) * 1000

        snapshot = {
            "user_id": user_id,
            "generated_at": time.time(),
            "duration_ms": round(duration_ms, 2),
            "hero": {
                "content_id": 1,
                "title": "Inception",
                "backdrop_url": "https://image.tmdb.org/t/p/w1280/8ZTVqvKDQ8emSGUEMjsS4yHA84.jpg",
                "overview": "Cobb, a skilled thief who commits corporate espionage..."
            },
            "shelves": shelves
        }

        self._snapshots[user_id] = snapshot
        return snapshot

    def get_precomputed_home_slate(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self._snapshots.get(user_id)
