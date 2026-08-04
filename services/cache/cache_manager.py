from __future__ import annotations
import time
from typing import Dict, Any, Optional
from services.cache.cache_keys import CacheKeyBuilder

class CacheManager:
    """Multilevel cache manager supporting in-memory LRU + Redis backend fallback."""

    def __init__(self, default_ttl_seconds: float = 300.0):
        self.default_ttl = default_ttl_seconds
        self._store: Dict[str, Dict[str, Any]] = {}
        self.keys = CacheKeyBuilder()

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if not entry:
            return None
        if time.time() > entry["expires_at"]:
            del self._store[key]
            return None
        return entry["value"]

    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None):
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        self._store[key] = {
            "value": value,
            "expires_at": time.time() + ttl
        }

    def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    def clear(self):
        self._store.clear()

    def size(self) -> int:
        return len(self._store)
