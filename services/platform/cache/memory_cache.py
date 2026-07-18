import time
from typing import Any, Optional, Dict

class MemoryCache:
    """Simple LRU-like memory cache with TTL."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.store: Dict[str, Dict[str, Any]] = {}
        
    def get(self, key: str) -> Optional[Any]:
        if key in self.store:
            entry = self.store[key]
            if time.time() > entry["expiry"]:
                self.delete(key)
                return None
            return entry["value"]
        return None
        
    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        if len(self.store) >= self.max_size:
            # Simple eviction: clear expired or randomly delete one
            self._evict()
            
        self.store[key] = {
            "value": value,
            "expiry": time.time() + ttl_seconds
        }
        
    def delete(self, key: str):
        if key in self.store:
            del self.store[key]
            
    def _evict(self):
        # Evict expired first
        now = time.time()
        expired = [k for k, v in self.store.items() if v["expiry"] < now]
        for k in expired:
            del self.store[k]
            
        # If still full, pop an arbitrary item
        if len(self.store) >= self.max_size and self.store:
            self.store.pop(next(iter(self.store)))
