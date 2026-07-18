from typing import Any, Optional, Dict
from .memory_cache import MemoryCache
from .cache_metrics import CacheMetrics
from services.platform.config.settings import settings
from services.platform.config.feature_flags import PlatformFlags

class CacheManager:
    """Manages separate caches for different purposes."""
    
    def __init__(self):
        self.enabled = PlatformFlags.ENABLE_CACHE
        
        self.caches = {
            "query": MemoryCache(max_size=500),
            "candidate": MemoryCache(max_size=500),
            "graph": MemoryCache(max_size=1000),
            "profile": MemoryCache(max_size=500),
            "recommendation": MemoryCache(max_size=200)
        }
        
        self.metrics = {
            name: CacheMetrics() for name in self.caches
        }
        
    def get(self, cache_name: str, key: str) -> Optional[Any]:
        if not self.enabled or cache_name not in self.caches:
            return None
            
        value = self.caches[cache_name].get(key)
        if value is not None:
            self.metrics[cache_name].record_hit()
        else:
            self.metrics[cache_name].record_miss()
            
        return value
        
    def set(self, cache_name: str, key: str, value: Any, ttl_seconds: int = None):
        if not self.enabled or cache_name not in self.caches:
            return
            
        ttl = ttl_seconds if ttl_seconds is not None else settings.CACHE_DEFAULT_TTL
        self.caches[cache_name].set(key, value, ttl)
        
    def get_metrics(self) -> Dict[str, Dict[str, float]]:
        return {
            name: metrics.get_metrics()
            for name, metrics in self.metrics.items()
        }
