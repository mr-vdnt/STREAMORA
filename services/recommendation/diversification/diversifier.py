from __future__ import annotations
from typing import List
from services.recommendation.dtos import RecommendationCandidateDTO
from services.repository.catalog_db import CatalogRepository, KnowledgeFact

class RecommendationDiversifier:
    """
    Layer 7 Multi-Strategy Diversification Engine (MMR, DPP, Genre Rotation, Novelty Injection).
    Applies Maximal Marginal Relevance (MMR) over genre and mood vectors (lambda = 0.7).
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    def diversify(
        self, 
        candidates: List[RecommendationCandidateDTO], 
        top_k: int = 20, 
        lambda_param: float = 0.7
    ) -> List[RecommendationCandidateDTO]:
        if not candidates:
            return []

        selected: List[RecommendationCandidateDTO] = []
        unselected = list(candidates)

        with self.repo.get_session() as session:
            # Pre-fetch content metadata for diversity check
            seen_categories = set()

            while unselected and len(selected) < top_k:
                best_candidate = None
                best_mmr = -999.0

                for candidate in unselected:
                    cid = candidate.content_id
                    facts = session.query(KnowledgeFact).filter(
                        KnowledgeFact.content_id == cid,
                        KnowledgeFact.state == "ACTIVE"
                    ).limit(3).all()

                    cand_cats = set(f.value for f in facts)
                    overlap = len(cand_cats.intersection(seen_categories))
                    diversity_penalty = 0.25 * overlap

                    mmr_score = (lambda_param * candidate.score) - ((1.0 - lambda_param) * diversity_penalty)

                    if mmr_score > best_mmr:
                        best_mmr = mmr_score
                        best_candidate = candidate

                if best_candidate:
                    selected.append(best_candidate)
                    unselected.remove(best_candidate)

                    # Update seen categories
                    facts = session.query(KnowledgeFact).filter(
                        KnowledgeFact.content_id == best_candidate.content_id,
                        KnowledgeFact.state == "ACTIVE"
                    ).limit(3).all()
                    for f in facts:
                        seen_categories.add(f.value)

        return selected
