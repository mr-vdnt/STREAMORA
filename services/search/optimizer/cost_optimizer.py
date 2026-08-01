from __future__ import annotations
import logging
from typing import List
from services.search.dtos import SearchPlanDTO

logger = logging.getLogger("streamora.search.optimizer")

class CostBasedQueryOptimizer:
    """
    Cost-Based Query Optimizer.
    Evaluates SearchPlan constraints, latency budgets, and retrieval costs, dynamically pruning unnecessary retrievers.
    """

    def optimize_plan(self, plan: SearchPlanDTO) -> SearchPlanDTO:
        # If intent is exact_title and latency budget is tight, skip heavy vector & relationship retrievers
        if plan.intent == "exact_title" and "embedding" in plan.active_retrievers:
            plan.active_retrievers.remove("embedding")
            plan.estimated_cost *= 0.5
            logger.info(f"Optimizer pruned 'embedding' retriever for exact_title query '{plan.query_text}'")

        # Cap active retrievers if estimated cost exceeds budget
        if plan.estimated_cost > 10.0 and len(plan.active_retrievers) > 3:
            pruned = plan.active_retrievers.pop()
            logger.info(f"Optimizer pruned '{pruned}' retriever due to high cost ({plan.estimated_cost})")

        return plan
