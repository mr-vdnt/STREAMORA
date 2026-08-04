from __future__ import annotations
from typing import Dict, Any, Optional
from services.feature_store.feature_registry import EnterpriseFeatureRegistry
from services.feature_store.feature_cache import EnterpriseFeatureCache
from services.feature_store.feature_materializer import EnterpriseFeatureMaterializer

class EnterpriseFeatureProvider:
    """Unified high-speed Feature Provider serving Search, Recommendation, Hero, and Discovery platforms."""

    def __init__(self):
        self.registry = EnterpriseFeatureRegistry()
        self.cache = EnterpriseFeatureCache()
        self.materializer = EnterpriseFeatureMaterializer(self.registry, self.cache)

    def get_content_features(self, content_id: int) -> Dict[str, Any]:
        cached = self.cache.get_features("content", content_id)
        if cached:
            return cached
        return self.materializer.materialize_content_features(content_id)

    def get_user_features(self, user_id: str) -> Dict[str, Any]:
        cached = self.cache.get_features("user", user_id)
        if cached:
            return cached

        user_vector = {
            "user_id": user_id,
            "genre_affinities": {"Sci-Fi": 0.95, "Action": 0.85},
            "theme_affinities": {"dream": 0.90},
            "completion_rate": 0.88
        }
        self.cache.set_features("user", user_id, user_vector)
        return user_vector
