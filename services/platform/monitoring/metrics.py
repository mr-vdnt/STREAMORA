import time
from typing import Dict, Any

class MetricsRegistry:
    """Simple in-memory metrics registry for tracking counters and gauges."""
    def __init__(self):
        self.counters: Dict[str, int] = {}
        self.timings: Dict[str, list] = {}
        
    def increment(self, metric: str, amount: int = 1):
        if metric not in self.counters:
            self.counters[metric] = 0
        self.counters[metric] += amount
        
    def record_time(self, metric: str, ms: float):
        if metric not in self.timings:
            self.timings[metric] = []
        self.timings[metric].append(ms)
        
    def get_snapshot(self) -> Dict[str, Any]:
        snapshot = {"counters": dict(self.counters), "timings_avg_ms": {}}
        for metric, times in self.timings.items():
            if times:
                snapshot["timings_avg_ms"][metric] = round(sum(times) / len(times), 2)
        return snapshot

# Global metrics registry
metrics_registry = MetricsRegistry()
