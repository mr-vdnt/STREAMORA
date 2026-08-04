from __future__ import annotations
from typing import Dict, Any, List
from services.feature_store.feature_registry import EnterpriseFeatureRegistry
from services.feature_store.feature_cache import EnterpriseFeatureCache
from services.feature_store.feature_repository import EnterpriseFeatureRepository

class EnterpriseFeatureMaterializer:
    """Automated materialization pipeline computing and vectorizing entity features."""

    def __init__(
        self,
        registry: EnterpriseFeatureRegistry = None,
        cache: EnterpriseFeatureCache = None,
        repository: EnterpriseFeatureRepository = None
    ):
        self.registry = registry or EnterpriseFeatureRegistry()
        self.cache = cache or EnterpriseFeatureCache()
        self.repository = repository or EnterpriseFeatureRepository()

    def materialize_content_features(self, content_id: int) -> Dict[str, Any]:
        # Compute/fetch features
        db_features = self.repository.get_content_features(content_id)

        # Vectorize & normalize
        feature_vector = {
            "content_id": content_id,
            "popularity_score": float(db_features.get("popularity_score", 0.5)),
            "quality_rating": float(db_features.get("quality_rating", 7.5)),
            "freshness_score": float(db_features.get("freshness_score", 0.8)),
            "knowledge_fact_count": int(db_features.get("knowledge_fact_count", 10)),
            "dense_vector": [0.1] * 128
        }

        # Cache materialized feature vector
        self.cache.set_features("content", content_id, feature_vector)
        self.repository.save_content_features(content_id, db_features)
        return feature_vector
