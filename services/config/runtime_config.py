from __future__ import annotations
import os
from typing import Dict, Any

class RuntimeConfigService:
    """Centralized runtime configuration manager."""

    def __init__(self):
        self._config: Dict[str, Any] = {
            "environment": os.environ.get("STREAMORA_ENV", "production"),
            "cdn_base_url": os.environ.get("STREAMORA_CDN_URL", "https://cdn.streamora.ai"),
            "max_home_feed_latency_ms": 500.0,
            "max_recommendation_candidates": 100,
            "default_hls_quality": "1080p",
            "jwt_token_ttl_hours": 168
        }

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        self._config[key] = value

    def get_all(self) -> Dict[str, Any]:
        return self._config.copy()
