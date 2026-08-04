from __future__ import annotations
import time
from typing import Dict, Any, Optional

class EnterpriseFeatureCache:
    """Low-latency in-memory and Redis feature vector cache."""

    def __init__(self, ttl_seconds: float = 600.0):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _build_key(self, entity_type: str, entity_id: str | int) -> str:
        return f"feature_vector:{entity_type}:{entity_id}"

    def get_features(self, entity_type: str, entity_id: str | int) -> Optional[Dict[str, Any]]:
        key = self._build_key(entity_type, entity_id)
        entry = self._cache.get(key)
        if not entry:
            return None
        if time.time() > entry["expires_at"]:
            del self._cache[key]
            return None
        return entry["features"]

    def set_features(self, entity_type: str, entity_id: str | int, features: Dict[str, Any], ttl: Optional[float] = None):
        key = self._build_key(entity_type, entity_id)
        expires_at = time.time() + (ttl or self.ttl_seconds)
        self._cache[key] = {
            "features": features,
            "expires_at": expires_at
        }

    def invalidate(self, entity_type: str, entity_id: str | int):
        key = self._build_key(entity_type, entity_id)
        if key in self._cache:
            del self._cache[key]
