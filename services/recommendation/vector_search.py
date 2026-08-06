from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class ContentEmbeddingVector:
    content_id: int
    dimension: int = 768
    vector: List[float] = field(default_factory=list)

class VectorSearchEngine:
    """
    768-Dimensional Dense Embedding Vector Search Engine.
    Computes cosine similarity between content vectors for nearest neighbor candidate retrieval.
    """

    def __init__(self):
        self._index: Dict[int, ContentEmbeddingVector] = {}

    def index_vector(self, embedding: ContentEmbeddingVector):
        self._index[embedding.content_id] = embedding

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm_v1 = math.sqrt(sum(a * a for a in v1))
        norm_v2 = math.sqrt(sum(b * b for b in v2))
        if norm_v1 == 0.0 or norm_v2 == 0.0:
            return 0.0
        return dot_product / (norm_v1 * norm_v2)

    def search_nearest_neighbors(self, target_vector: List[float], top_k: int = 10, exclude_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        exclude = set(exclude_ids or [])
        results = []
        for content_id, emb in self._index.items():
            if content_id in exclude:
                continue
            sim = self.cosine_similarity(target_vector, emb.vector)
            results.append({"content_id": content_id, "similarity": sim})

        return sorted(results, key=lambda x: x["similarity"], reverse=True)[:top_k]
