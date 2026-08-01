from __future__ import annotations
from typing import List
from services.recommendation.contracts import BaseCandidateGenerator
from services.recommendation.dtos import RecommendationPlanDTO, RecommendationCandidateDTO, UserIntelligenceProfileDTO
from services.repository.catalog_db import CatalogRepository, ContentStatistics

class TrendingCandidateGenerator(BaseCandidateGenerator):
    """
    Trending & Velocity Candidate Generator.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    @property
    def name(self) -> str:
        return "trending"

    def supports(self, plan: RecommendationPlanDTO) -> bool:
        return True

    def estimate_cost(self) -> float:
        return 0.8

    async def generate_candidates(
        self, 
        plan: RecommendationPlanDTO, 
        profile: UserIntelligenceProfileDTO
    ) -> List[RecommendationCandidateDTO]:
        candidates: List[RecommendationCandidateDTO] = []
        with self.repo.get_session() as session:
            stats = session.query(ContentStatistics).order_by(ContentStatistics.popularity.desc()).limit(15).all()
            for s in stats:
                candidates.append(RecommendationCandidateDTO(
                    content_id=s.content_id,
                    generator_name=self.name,
                    score=0.80,
                    reason="Trending globally across Streamora right now",
                    provenance_metadata={"popularity": s.popularity}
                ))
        return candidates
