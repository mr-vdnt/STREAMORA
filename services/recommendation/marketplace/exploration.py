from __future__ import annotations
import random
from typing import List
from services.recommendation.contracts import BaseCandidateGenerator
from services.recommendation.dtos import RecommendationPlanDTO, RecommendationCandidateDTO, UserIntelligenceProfileDTO
from services.repository.catalog_db import CatalogRepository, Content

class ExplorationCandidateGenerator(BaseCandidateGenerator):
    """
    Serendipity & Novelty Exploration Generator for long-tail discovery.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    @property
    def name(self) -> str:
        return "exploration"

    def supports(self, plan: RecommendationPlanDTO) -> bool:
        return True

    def estimate_cost(self) -> float:
        return 0.5

    async def generate_candidates(
        self, 
        plan: RecommendationPlanDTO, 
        profile: UserIntelligenceProfileDTO
    ) -> List[RecommendationCandidateDTO]:
        candidates: List[RecommendationCandidateDTO] = []
        with self.repo.get_session() as session:
            contents = session.query(Content).filter(Content.is_deleted == False).limit(30).all()
            sampled = random.sample(contents, min(5, len(contents))) if contents else []
            for c in sampled:
                candidates.append(RecommendationCandidateDTO(
                    content_id=c.id,
                    generator_name=self.name,
                    score=0.70,
                    reason="Serendipity pick: Explore something new",
                    provenance_metadata={"exploration": True}
                ))
        return candidates
