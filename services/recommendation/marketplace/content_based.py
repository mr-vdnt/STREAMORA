from __future__ import annotations
from typing import List
from services.recommendation.contracts import BaseCandidateGenerator
from services.recommendation.dtos import RecommendationPlanDTO, RecommendationCandidateDTO, UserIntelligenceProfileDTO
from services.repository.catalog_db import CatalogRepository, KnowledgeFact

class ContentBasedCandidateGenerator(BaseCandidateGenerator):
    """
    Content-based generator matching user's preferred KnowledgeFact themes and moods.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    @property
    def name(self) -> str:
        return "content_based"

    def supports(self, plan: RecommendationPlanDTO) -> bool:
        return True

    def estimate_cost(self) -> float:
        return 1.5

    async def generate_candidates(
        self, 
        plan: RecommendationPlanDTO, 
        profile: UserIntelligenceProfileDTO
    ) -> List[RecommendationCandidateDTO]:
        candidates: List[RecommendationCandidateDTO] = []
        top_themes = set(profile.theme_affinities.keys())
        top_moods = set(profile.mood_affinities.keys())

        with self.repo.get_session() as session:
            facts = session.query(KnowledgeFact).filter(KnowledgeFact.state == "ACTIVE").all()
            matched_map = {}

            for f in facts:
                val = str(f.value).lower().replace("genre-", "").replace("-", " ")
                if any(t in val for t in top_themes) or any(m in val for m in top_moods):
                    cid = f.content_id
                    if cid not in matched_map:
                        matched_map[cid] = []
                    matched_map[cid].append(val)

            for cid, matched_vals in matched_map.items():
                candidates.append(RecommendationCandidateDTO(
                    content_id=cid,
                    generator_name=self.name,
                    score=0.90,
                    reason=f"Matches your affinity for: {', '.join(matched_vals[:2])}",
                    provenance_metadata={"matched_facts": matched_vals}
                ))

        return candidates
