from functools import lru_cache
from typing import Dict, Any, List

class GraphCache:
    """A lightweight cache for expensive graph traversals and similarity scores."""
    
    def __init__(self):
        # We can implement a custom LRU or just use dictionaries for now
        # and clear them when the graph rebuilds.
        self._similarity_cache: Dict[str, float] = {}
        self._related_movies_cache: Dict[str, List[int]] = {}
        
    def get_similarity(self, content_id_1: int, content_id_2: int) -> float:
        key = self._make_sim_key(content_id_1, content_id_2)
        return self._similarity_cache.get(key, -1.0)
        
    def set_similarity(self, content_id_1: int, content_id_2: int, score: float) -> None:
        key = self._make_sim_key(content_id_1, content_id_2)
        self._similarity_cache[key] = score
        
    def get_related_movies(self, content_id: int) -> List[int]:
        return self._related_movies_cache.get(str(content_id))
        
    def set_related_movies(self, content_id: int, related: List[int]) -> None:
        self._related_movies_cache[str(content_id)] = related
        
    def _make_sim_key(self, c1: int, c2: int) -> str:
        # Sort so that (1, 2) and (2, 1) use the same key
        sorted_ids = sorted([c1, c2])
        return f"{sorted_ids[0]}_{sorted_ids[1]}"
        
    def clear(self):
        self._similarity_cache.clear()
        self._related_movies_cache.clear()
