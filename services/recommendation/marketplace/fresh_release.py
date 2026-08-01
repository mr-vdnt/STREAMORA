from __future__ import annotations
from typing import List
from services.recommendation.contracts import BaseCandidateGenerator
from services.recommendation.dtos import RecommendationPlanDTO, RecommendationCandidateDTO, UserIntelligenceProfileDTO
from services.repository.catalog_db import CatalogRepository, ContentMetadata

class FreshReleaseCandidateGenerator(BaseCandidateGenerator):
    """
    Fresh Release Candidate Generator for recently released movies and series.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    @property
    def name(self) -> str:
        return "fresh_release"

    def supports(self, plan: RecommendationPlanDTO) -> bool:
        return plan.slate_type in ["new_releases", "home_feed", "personalized_home"]

    def estimate_cost(self) -> float:
        return 0.9

    async def generate_candidates(
        self, 
        plan: RecommendationPlanDTO, 
        profile: UserIntelligenceProfileDTO
    ) -> List[RecommendationCandidateDTO]:
        candidates: List[RecommendationCandidateDTO] = []
        with self.repo.get_session() as session:
            metas = session.query(ContentMetadata).order_by(ContentMetadata.release_date.desc()).limit(15).all()
            for m in metas:
                candidates.append(RecommendationCandidateDTO(
                    content_id=m.content_id,
                    generator_name=self.name,
                    score=0.82,
                    reason=f"New Release ({m.release_date or 'Recent'})",
                    provenance_metadata={"release_date": m.release_date}
                ))
        return candidates
