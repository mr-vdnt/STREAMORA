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

    @staticmethod
    def mrr_at_k(recommended_ids: List[int], ground_truth_ids: Set[int], k: int = 10) -> float:
        """Mean Reciprocal Rank (MRR) evaluating the position of the first relevant recommendation."""
        for i, item_id in enumerate(recommended_ids[:k]):
            if item_id in ground_truth_ids:
                return 1.0 / (i + 1)
        return 0.0

    @staticmethod
    def hit_rate_at_k(recommended_ids: List[int], ground_truth_ids: Set[int], k: int = 10) -> float:
        """HitRate@K binary indicator if at least 1 ground truth item is present in top-K."""
        top_k = set(recommended_ids[:k])
        return 1.0 if len(top_k.intersection(ground_truth_ids)) > 0 else 0.0

    @staticmethod
    def map_at_k(recommended_ids: List[int], ground_truth_ids: Set[int], k: int = 10) -> float:
        """Mean Average Precision (MAP@K)."""
        if not ground_truth_ids:
            return 0.0
        hits = 0
        sum_precisions = 0.0
        for i, item_id in enumerate(recommended_ids[:k]):
            if item_id in ground_truth_ids:
                hits += 1
                sum_precisions += hits / (i + 1)
        return sum_precisions / min(len(ground_truth_ids), k)
