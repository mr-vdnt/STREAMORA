from __future__ import annotations
import hashlib
from typing import Dict, List, Optional
from services.recommendation.dtos import RecommendationPlanDTO, UserIntelligenceProfileDTO
from services.recommendation.taxonomy import SlateType

class RecommendationPlanner:
    """
    Layer 2 Recommendation Planner Engine.
    Transforms slate requests and user profile into structured RecommendationPlanDTO instances.
    """

    def create_plan(
        self, 
        user_id: str, 
        slate_type: str = "personalized_home", 
        context_item_id: Optional[int] = None
    ) -> RecommendationPlanDTO:
        active_generators = ["collaborative", "content_based", "trending"]
        allocated_counts = {"collaborative": 30, "content_based": 30, "trending": 20}

        if slate_type == SlateType.BECAUSE_YOU_WATCHED.value or context_item_id is not None:
            active_generators = ["content_based", "knowledge_graph", "collaborative"]
            allocated_counts = {"content_based": 50, "knowledge_graph": 30, "collaborative": 20}

        elif slate_type == SlateType.TRENDING_FOR_YOU.value:
            active_generators = ["trending", "fresh_release", "collaborative"]
            allocated_counts = {"trending": 50, "fresh_release": 30, "collaborative": 20}

        elif slate_type == SlateType.CONTINUE_WATCHING.value:
            active_generators = ["continue_watching"]
            allocated_counts = {"continue_watching": 10}

        plan_data = f"{user_id}:{slate_type}:{context_item_id}:{sorted(active_generators)}"
        plan_hash = hashlib.sha256(plan_data.encode('utf-8')).hexdigest()[:16]

        return RecommendationPlanDTO(
            user_id=user_id,
            slate_type=slate_type,
            context_item_id=context_item_id,
            active_generators=active_generators,
            allocated_counts=allocated_counts,
            estimated_cost=len(active_generators) * 1.2,
            latency_budget_ms=80.0,
            plan_hash=plan_hash
        )
