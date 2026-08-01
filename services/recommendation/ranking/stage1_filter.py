from __future__ import annotations
from typing import List, Set
from services.recommendation.dtos import RecommendationCandidateDTO

class HardCandidateFilter:
    """
    Stage 1 Hard Filtering (filters out deleted items, age-restricted items, or dismissed content).
    """

    def filter(
        self, 
        candidates: List[RecommendationCandidateDTO], 
        excluded_ids: Set[int] = None
    ) -> List[RecommendationCandidateDTO]:
        excluded = excluded_ids or set()
        return [c for c in candidates if c.content_id not in excluded]
