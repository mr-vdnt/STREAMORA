from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
from services.recommendation.dtos import RecommendationPlanDTO, RecommendationCandidateDTO, UserIntelligenceProfileDTO

class BaseCandidateGenerator(ABC):
    """Abstract Base Class for pluggable candidate generators in the Candidate Marketplace."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this candidate generator."""
        ...

    @abstractmethod
    def supports(self, plan: RecommendationPlanDTO) -> bool:
        """Check if this generator supports the given RecommendationPlan."""
        ...

    @abstractmethod
    def estimate_cost(self) -> float:
        """Estimate relative computation cost (0.1 to 10.0)."""
        ...

    @abstractmethod
    async def generate_candidates(
        self, 
        plan: RecommendationPlanDTO, 
        profile: UserIntelligenceProfileDTO
    ) -> List[RecommendationCandidateDTO]:
        """Generate recommendation candidate DTOs for a plan and user profile."""
        ...
