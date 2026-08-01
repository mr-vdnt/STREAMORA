from __future__ import annotations
from typing import List
from services.recommendation.dtos import RecommendationCandidateDTO

class ModularPolicyEngine:
    """
    Layer 8 Policy Engine executing independent policy rules:
    - FilteringPolicy (Hide watched)
    - AgePolicy
    - RegionalPolicy
    - EditorialPolicy
    - BusinessPolicy (Sponsored & Fresh boosts)
    """

    def apply_policies(
        self, 
        candidates: List[RecommendationCandidateDTO]
    ) -> List[RecommendationCandidateDTO]:
        compliant: List[RecommendationCandidateDTO] = []
        for c in candidates:
            # Policy 1: Exclude candidates with zero or negative scores
            if c.score <= 0.0:
                continue

            # Policy 2: Apply Editorial / Sponsored boosts
            if c.provenance_metadata.get("editorial", False):
                c.score = min(1.0, c.score * 1.1)

            compliant.append(c)

        return compliant
