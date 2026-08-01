from __future__ import annotations
from typing import List, Tuple
from services.search.dtos import SearchPlanDTO, RetrievedCandidateDTO, RankingFeatureVectorDTO
from services.search.ranking.feature_extractor import RankingFeatureExtractor

class HeuristicRanker:
    """
    Multi-stage ranking pipeline engine.
    Computes final rank scores using multi-signal weights:
    FinalScore = 0.4*lexical + 0.3*knowledge + 0.15*popularity + 0.1*quality + 0.05*freshness
    """

    def __init__(self, extractor: RankingFeatureExtractor = None):
        self.extractor = extractor or RankingFeatureExtractor()

    def rank(self, candidates: List[RetrievedCandidateDTO], plan: SearchPlanDTO) -> List[Tuple[RetrievedCandidateDTO, RankingFeatureVectorDTO]]:
        ranked_pairs: List[Tuple[RetrievedCandidateDTO, RankingFeatureVectorDTO]] = []

        for candidate in candidates:
            fv = self.extractor.extract(candidate, plan)

            # Weight distribution based on intent
            if plan.intent == "exact_title":
                w_lex, w_know, w_pop, w_qual = 0.70, 0.10, 0.10, 0.10
            elif plan.intent == "theme_mood_query":
                w_lex, w_know, w_pop, w_qual = 0.20, 0.50, 0.15, 0.15
            else:
                w_lex, w_know, w_pop, w_qual = 0.40, 0.30, 0.15, 0.15

            final_score = (
                (fv.lexical_score * w_lex) +
                (fv.knowledge_overlap_score * w_know) +
                (fv.popularity_score * w_pop) +
                (fv.quality_score * w_qual) +
                (fv.freshness_score * 0.05)
            )

            fv.final_rank_score = round(min(1.0, final_score), 4)
            candidate.score = fv.final_rank_score
            ranked_pairs.append((candidate, fv))

        ranked_pairs.sort(key=lambda x: x[1].final_rank_score, reverse=True)
        return ranked_pairs
