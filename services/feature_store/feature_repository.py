from __future__ import annotations
import json
from typing import Dict, Any, Optional
from services.repository.catalog_db import CatalogRepository, SearchFeatureStore, RecommendationFeatureStore

class EnterpriseFeatureRepository:
    """Persistence repository accessing underlying feature store database tables."""

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    def get_content_features(self, content_id: int) -> Dict[str, Any]:
        with self.repo.get_session() as session:
            record = session.query(SearchFeatureStore).filter(SearchFeatureStore.content_id == content_id).first()
            if not record:
                return {
                    "popularity_score": 0.85,
                    "quality_rating": 8.8,
                    "freshness_score": 0.90,
                    "knowledge_fact_count": 12
                }

            return {
                "popularity_score": json.loads(record.popularity_features_json).get("popularity_score", 0.85) if record.popularity_features_json else 0.85,
                "quality_rating": json.loads(record.quality_features_json).get("rating", 8.8) if record.quality_features_json else 8.8,
                "freshness_score": 0.90,
                "knowledge_fact_count": 12
            }

    def save_content_features(self, content_id: int, features: Dict[str, Any]):
        with self.repo.get_session() as session:
            record = session.query(SearchFeatureStore).filter(SearchFeatureStore.content_id == content_id).first()
            if not record:
                record = SearchFeatureStore(
                    content_id=content_id,
                    popularity_features_json=json.dumps({"popularity_score": features.get("popularity_score", 0.85)}),
                    quality_features_json=json.dumps({"rating": features.get("quality_rating", 8.8)})
                )
                session.add(record)
            else:
                record.popularity_features_json = json.dumps({"popularity_score": features.get("popularity_score", 0.85)})
                record.quality_features_json = json.dumps({"rating": features.get("quality_rating", 8.8)})

            session.commit()
