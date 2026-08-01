from __future__ import annotations
import math
from typing import List

class SearchEvaluator:
    """
    Search Platform IR Quality & Operational Metrics Evaluator.
    Computes NDCG@K, MRR, Precision@K, Recall@K, and Latency metrics.
    """

    @staticmethod
    def compute_mrr(relevant_indices: List[int]) -> float:
        """Mean Reciprocal Rank given 0-indexed positions of relevant hits."""
        if not relevant_indices:
            return 0.0
        first_rel = min(relevant_indices)
        return 1.0 / (first_rel + 1)

    @staticmethod
    def compute_precision_at_k(relevant_indices: List[int], k: int = 10) -> float:
        rel_in_k = [i for i in relevant_indices if i < k]
        return len(rel_in_k) / float(k)

    @staticmethod
    def compute_ndcg_at_k(relevance_scores: List[float], k: int = 10) -> float:
        """Normalized Discounted Cumulative Gain at rank K."""
        k = min(k, len(relevance_scores))
        if k == 0:
            return 0.0

        dcg = sum(
            (math.pow(2, rel) - 1.0) / math.log2(idx + 2)
            for idx, rel in enumerate(relevance_scores[:k])
        )

        ideal_scores = sorted(relevance_scores, reverse=True)[:k]
        idcg = sum(
            (math.pow(2, rel) - 1.0) / math.log2(idx + 2)
            for idx, rel in enumerate(ideal_scores)
        )

        return (dcg / idcg) if idcg > 0 else 0.0
