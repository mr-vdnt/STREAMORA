from typing import Dict

class CacheMetrics:
    def __init__(self):
        self.hits = 0
        self.misses = 0
        
    def record_hit(self):
        self.hits += 1
        
    def record_miss(self):
        self.misses += 1
        
    def get_metrics(self) -> Dict[str, float]:
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0.0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 4)
        }
