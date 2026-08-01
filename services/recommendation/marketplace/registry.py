from __future__ import annotations
import asyncio
import logging
from typing import Dict, List
from services.recommendation.contracts import BaseCandidateGenerator
from services.recommendation.dtos import RecommendationPlanDTO, RecommendationCandidateDTO, UserIntelligenceProfileDTO

logger = logging.getLogger("streamora.recommendation.marketplace")

class CandidateMarketplace:
    """
    Candidate Generator Marketplace.
    Manages pluggable candidate generators and executes parallel candidate generation across active strategies.
    """

    def __init__(self):
        self._generators: Dict[str, BaseCandidateGenerator] = {}

    def register(self, generator: BaseCandidateGenerator) -> None:
        self._generators[generator.name] = generator
        logger.info(f"Registered Recommendation Candidate Generator: '{generator.name}' (Cost: {generator.estimate_cost()})")

    async def execute_generation(
        self, 
        plan: RecommendationPlanDTO, 
        profile: UserIntelligenceProfileDTO
    ) -> List[RecommendationCandidateDTO]:
        active_instances = [
            g for name, g in self._generators.items()
            if name in plan.active_generators and g.supports(plan)
        ]

        if not active_instances:
            logger.warning(f"No active candidate generators matched plan for slate '{plan.slate_type}'")
            return []

        tasks = [g.generate_candidates(plan, profile) for g in active_instances]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_candidates: List[RecommendationCandidateDTO] = []
        for c_list in results:
            if isinstance(c_list, list):
                all_candidates.extend(c_list)
            elif isinstance(c_list, Exception):
                logger.error(f"Candidate generator error: {c_list}")

        return all_candidates
