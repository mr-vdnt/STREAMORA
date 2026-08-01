from __future__ import annotations
import json
from typing import Any, Dict
from services.repository.catalog_db import CatalogRepository, RecommendationFeatureStore, ContentStatistics

class RecommendationFeatureStoreService:
    """
    Materialized Feature Store accessor for offline & online recommendation ranking features.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    def get_content_features(self, content_id: int) -> Dict[str, Any]:
        with self.repo.get_session() as session:
            fs = session.query(RecommendationFeatureStore).filter(RecommendationFeatureStore.content_id == content_id).first()
            if fs:
                return {
                    "content_id": fs.content_id,
                    "content_features": json.loads(fs.content_features_json) if fs.content_features_json else {},
                    "interaction_features": json.loads(fs.interaction_features_json) if fs.interaction_features_json else {},
                    "graph_features": json.loads(fs.graph_features_json) if fs.graph_features_json else {}
                }

            stats = session.query(ContentStatistics).filter(ContentStatistics.content_id == content_id).first()
            return {
                "content_id": content_id,
                "content_features": {"rating": stats.average_rating if stats else 0.0},
                "interaction_features": {"popularity": stats.popularity if stats else 0.0},
                "graph_features": {"franchise_depth": 1}
            }
