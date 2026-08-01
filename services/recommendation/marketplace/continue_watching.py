from __future__ import annotations
from typing import List
from services.recommendation.contracts import BaseCandidateGenerator
from services.recommendation.dtos import RecommendationPlanDTO, RecommendationCandidateDTO, UserIntelligenceProfileDTO
from services.repository.catalog_db import CatalogRepository, UserInteractionEvent

class ContinueWatchingCandidateGenerator(BaseCandidateGenerator):
    """
    Continue Watching Generator for partially watched series and movies.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    @property
    def name(self) -> str:
        return "continue_watching"

    def supports(self, plan: RecommendationPlanDTO) -> bool:
        return plan.slate_type in ["continue_watching", "home_feed", "personalized_home"]

    def estimate_cost(self) -> float:
        return 0.6

    async def generate_candidates(
        self, 
        plan: RecommendationPlanDTO, 
        profile: UserIntelligenceProfileDTO
    ) -> List[RecommendationCandidateDTO]:
        candidates: List[RecommendationCandidateDTO] = []
        with self.repo.get_session() as session:
            events = session.query(UserInteractionEvent).filter(
                UserInteractionEvent.user_id == plan.user_id,
                UserInteractionEvent.event_type == "watch"
            ).order_by(UserInteractionEvent.created_at.desc()).limit(5).all()

            for evt in events:
                candidates.append(RecommendationCandidateDTO(
                    content_id=evt.content_id,
                    generator_name=self.name,
                    score=0.98,
                    reason="Resume watching where you left off",
                    provenance_metadata={"continue_watching": True}
                ))

        return candidates
