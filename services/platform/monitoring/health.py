from typing import Dict, Any
from services.platform.config.settings import settings

class HealthCheck:
    def __init__(self, movies_db: dict = None, cache_manager=None):
        self.movies_db = movies_db or {}
        self.cache_manager = cache_manager
        
    def check(self) -> Dict[str, Any]:
        """Provides status of critical platform dependencies."""
        db_ok = len(self.movies_db) > 0
        cache_ok = self.cache_manager is not None
        
        status = "ok" if (db_ok and cache_ok) else "degraded"
        if not db_ok:
            status = "critical"
            
        return {
            "status": status,
            "components": {
                "catalog": "ok" if db_ok else "failed",
                "cache": "ok" if cache_ok else "failed"
            },
            "environment": settings.ENV
        }
