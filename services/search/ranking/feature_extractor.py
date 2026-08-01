from __future__ import annotations
import math
from typing import Any, Dict
from services.search.dtos import SearchPlanDTO, RetrievedCandidateDTO, RankingFeatureVectorDTO
from services.search.ranking.feature_store import SearchFeatureStoreService

class RankingFeatureExtractor:
    """
    Extracts normalized RankingFeatureVectorDTO objects from SearchPlan, candidate fusion score, and SearchFeatureStore.
    """

    def __init__(self, feature_store: SearchFeatureStoreService = None):
        self.feature_store = feature_store or SearchFeatureStoreService()

    def extract(self, candidate: RetrievedCandidateDTO, plan: SearchPlanDTO) -> RankingFeatureVectorDTO:
        cid = candidate.content_id
        store_feats = self.feature_store.get_features(cid)

        pop = store_feats.get("popularity_features", {}).get("popularity", 0.0)
        rating = store_feats.get("quality_features", {}).get("average_rating", 0.0)

        # Lexical score vs Knowledge overlap score from fusion sources
        sources = candidate.provenance_metadata.get("sources", [])
        lexical_score = candidate.score if "lexical" in sources else 0.0
        knowledge_score = candidate.score if "knowledge_fact" in sources else 0.0

        pop_score = math.log(1.0 + pop) / 10.0
        quality_score = rating / 10.0

        return RankingFeatureVectorDTO(
            content_id=cid,
            lexical_score=lexical_score,
            knowledge_overlap_score=knowledge_score,
            popularity_score=min(1.0, pop_score),
            quality_score=min(1.0, quality_score),
            freshness_score=0.8,
            vector_similarity=0.75 if "embedding" in sources else 0.0
        )
