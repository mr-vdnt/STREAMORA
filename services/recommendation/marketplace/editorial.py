from __future__ import annotations
from typing import List
from services.recommendation.contracts import BaseCandidateGenerator
from services.recommendation.dtos import RecommendationPlanDTO, RecommendationCandidateDTO, UserIntelligenceProfileDTO
from services.repository.catalog_db import CatalogRepository, Content

class EditorialCandidateGenerator(BaseCandidateGenerator):
    """
    Editorial & Curated List Generator.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    @property
    def name(self) -> str:
        return "editorial"

    def supports(self, plan: RecommendationPlanDTO) -> bool:
        return True

    def estimate_cost(self) -> float:
        return 0.4

    async def generate_candidates(
        self, 
        plan: RecommendationPlanDTO, 
        profile: UserIntelligenceProfileDTO
    ) -> List[RecommendationCandidateDTO]:
        candidates: List[RecommendationCandidateDTO] = []
        with self.repo.get_session() as session:
            contents = session.query(Content).filter(Content.is_deleted == False).limit(5).all()
            for c in contents:
                candidates.append(RecommendationCandidateDTO(
                    content_id=c.id,
                    generator_name=self.name,
                    score=0.85,
                    reason="Curated Editor's Choice Spotlight",
                    provenance_metadata={"editorial": True}
                ))
        return candidates
