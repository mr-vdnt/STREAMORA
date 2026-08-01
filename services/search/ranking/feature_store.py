from __future__ import annotations
import json
from datetime import datetime
from typing import Any, Dict, Optional
from services.repository.catalog_db import CatalogRepository, SearchFeatureStore, ContentStatistics, IntelligenceProfile

class SearchFeatureStoreService:
    """
    SearchFeatureStore Service backing offline/online LTR ranking features.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    def get_features(self, content_id: int) -> Dict[str, Any]:
        with self.repo.get_session() as session:
            fs = session.query(SearchFeatureStore).filter(SearchFeatureStore.content_id == content_id).first()
            if fs:
                return {
                    "content_id": fs.content_id,
                    "knowledge_features": json.loads(fs.knowledge_features_json) if fs.knowledge_features_json else {},
                    "popularity_features": json.loads(fs.popularity_features_json) if fs.popularity_features_json else {},
                    "quality_features": json.loads(fs.quality_features_json) if fs.quality_features_json else {},
                    "graph_features": json.loads(fs.graph_features_json) if fs.graph_features_json else {}
                }

            # Fallback inline feature generation
            stats = session.query(ContentStatistics).filter(ContentStatistics.content_id == content_id).first()
            profile = session.query(IntelligenceProfile).filter(IntelligenceProfile.content_id == content_id).first()

            return {
                "content_id": content_id,
                "knowledge_features": {"fact_count": profile.fact_count if profile else 0},
                "popularity_features": {"popularity": stats.popularity if stats else 0.0},
                "quality_features": {"average_rating": stats.average_rating if stats else 0.0},
                "graph_features": {"relationship_count": 1}
            }
