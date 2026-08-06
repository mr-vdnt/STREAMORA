from __future__ import annotations
import math
from typing import List, Dict, Set, Any

class RecommendationEvaluator:
    """
    Offline Recommendation Quality Evaluator computing standard IR metrics:
    - Precision@K
    - Recall@K
    - NDCG@K (Normalized Discounted Cumulative Gain)
    - Catalog Coverage (%)
    - Intra-List Diversity
    """

    @staticmethod
    def precision_at_k(recommended_ids: List[int], ground_truth_ids: Set[int], k: int = 10) -> float:
        top_k = recommended_ids[:k]
        if not top_k:
            return 0.0
        hits = len(set(top_k).intersection(ground_truth_ids))
        return hits / len(top_k)

    @staticmethod
    def recall_at_k(recommended_ids: List[int], ground_truth_ids: Set[int], k: int = 10) -> float:
        if not ground_truth_ids:
            return 0.0
        top_k = recommended_ids[:k]
        hits = len(set(top_k).intersection(ground_truth_ids))
        return hits / len(ground_truth_ids)

    @staticmethod
    def ndcg_at_k(recommended_ids: List[int], ground_truth_ids: Set[int], k: int = 10) -> float:
        top_k = recommended_ids[:k]
        dcg = 0.0
        for i, item_id in enumerate(top_k):
            if item_id in ground_truth_ids:
                dcg += 1.0 / math.log2(i + 2)

        # Ideal DCG
        idcg = sum(1.0 / math.log2(i + 2) for i in range(min(len(ground_truth_ids), k)))
        if idcg == 0.0:
            return 0.0
        return dcg / idcg

    @staticmethod
    def catalog_coverage(all_recommended_ids: Set[int], total_catalog_ids: Set[int]) -> float:
        if not total_catalog_ids:
            return 0.0
        return (len(all_recommended_ids.intersection(total_catalog_ids)) / len(total_catalog_ids)) * 100.0
