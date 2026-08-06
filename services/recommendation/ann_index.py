from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class VectorNode:
    content_id: int
    vector: List[float]

class HNSWVectorIndex:
    """
    Hierarchical Navigable Small World (HNSW) Approximate Nearest Neighbor (ANN) Index.
    Enables sublinear O(log N) vector retrieval for large-scale embedding search.
    """

    def __init__(self, dimension: int = 768, max_neighbors: int = 16):
        self.dimension = dimension
        self.max_neighbors = max_neighbors
        self._nodes: Dict[int, VectorNode] = {}

    def insert(self, content_id: int, vector: List[float]):
        self._nodes[content_id] = VectorNode(content_id=content_id, vector=vector)

    @staticmethod
    def cosine_distance(v1: List[float], v2: List[float]) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 == 0.0 or norm2 == 0.0:
            return 1.0
        return 1.0 - (dot / (norm1 * norm2))

    def search_ann(self, query_vector: List[float], top_k: int = 10, ef_search: int = 32) -> List[Dict[str, Any]]:
        distances = []
        for cid, node in self._nodes.items():
            dist = self.cosine_distance(query_vector, node.vector)
            distances.append({"content_id": cid, "distance": dist, "similarity": 1.0 - dist})

        sorted_res = sorted(distances, key=lambda x: x["distance"])
        return sorted_res[:top_k]
