from __future__ import annotations
import logging
from services.recommendation.dtos import RecommendationPlanDTO

logger = logging.getLogger("streamora.recommendation.optimizer")

class RecommendationOptimizer:
    """
    Recommendation Optimizer.
    Dynamically adjusts candidate generator selection, item allocation counts, and latency budgets based on slate context.
    """

    def optimize_plan(self, plan: RecommendationPlanDTO) -> RecommendationPlanDTO:
        # If latency budget is tight, drop slow generators
        if plan.latency_budget_ms < 50.0 and "exploration" in plan.active_generators:
            plan.active_generators.remove("exploration")
            plan.estimated_cost *= 0.7
            logger.info(f"Optimizer pruned 'exploration' generator for user '{plan.user_id}' due to tight latency budget")

        return plan
