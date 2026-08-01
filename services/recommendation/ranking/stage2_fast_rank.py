from __future__ import annotations
from typing import List
from services.recommendation.dtos import RecommendationCandidateDTO, UserIntelligenceProfileDTO
from services.recommendation.ranking.feature_store import RecommendationFeatureStoreService

class FastHeuristicRanker:
    """
    Stage 2 Fast Heuristic Ranker computing Affinity x Quality scores.
    """

    def __init__(self, feature_store: RecommendationFeatureStoreService = None):
        self.feature_store = feature_store or RecommendationFeatureStoreService()

    def rank(
        self, 
        candidates: List[RecommendationCandidateDTO], 
        profile: UserIntelligenceProfileDTO
    ) -> List[RecommendationCandidateDTO]:
        for c in candidates:
            feats = self.feature_store.get_content_features(c.content_id)
            pop = feats.get("interaction_features", {}).get("popularity", 0.0)
            rating = feats.get("content_features", {}).get("rating", 0.0)

            quality_mult = (rating / 10.0) * 0.2 + 0.8
            c.score = round(min(1.0, c.score * quality_mult), 4)

        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates
