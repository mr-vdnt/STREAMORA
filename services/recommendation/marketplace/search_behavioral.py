from __future__ import annotations
from typing import List
from services.recommendation.contracts import BaseCandidateGenerator
from services.recommendation.dtos import RecommendationPlanDTO, RecommendationCandidateDTO, UserIntelligenceProfileDTO
from services.repository.catalog_db import CatalogRepository, SearchEvent

class SearchBehavioralCandidateGenerator(BaseCandidateGenerator):
    """
    Search Behavior Candidate Generator leveraging Phase 5 search query intent and click telemetry.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    @property
    def name(self) -> str:
        return "search_behavioral"

    def supports(self, plan: RecommendationPlanDTO) -> bool:
        return True

    def estimate_cost(self) -> float:
        return 1.2

    async def generate_candidates(
        self, 
        plan: RecommendationPlanDTO, 
        profile: UserIntelligenceProfileDTO
    ) -> List[RecommendationCandidateDTO]:
        candidates: List[RecommendationCandidateDTO] = []
        with self.repo.get_session() as session:
            events = session.query(SearchEvent).filter(SearchEvent.clicked_content_id.isnot(None)).limit(10).all()
            for evt in events:
                candidates.append(RecommendationCandidateDTO(
                    content_id=evt.clicked_content_id,
                    generator_name=self.name,
                    score=0.92,
                    reason=f"Based on your recent search for '{evt.query_text}'",
                    provenance_metadata={"search_query": evt.query_text, "intent": evt.parsed_intent}
                ))
        return candidates
