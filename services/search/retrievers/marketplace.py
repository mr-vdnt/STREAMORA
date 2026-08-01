from __future__ import annotations
import asyncio
import logging
from typing import Dict, List
from services.search.retrievers.base import BaseRetriever
from services.search.dtos import SearchPlanDTO, RetrievedCandidateDTO

logger = logging.getLogger("streamora.search.marketplace")

class RetrievalMarketplace:
    """
    Retrieval Marketplace Registry.
    Manages pluggable retrievers and executes candidates retrieval in parallel based on SearchPlan.
    """

    def __init__(self):
        self._retrievers: Dict[str, BaseRetriever] = {}

    def register(self, retriever: BaseRetriever) -> None:
        self._retrievers[retriever.name] = retriever
        logger.info(f"Registered Retrieval Plugin: '{retriever.name}' (Cost: {retriever.estimate_cost()})")

    async def execute_retrieval(self, plan: SearchPlanDTO) -> List[RetrievedCandidateDTO]:
        active_instances = [
            r for name, r in self._retrievers.items()
            if name in plan.active_retrievers and r.supports(plan)
        ]

        if not active_instances:
            logger.warning(f"No active retrievers matched plan for query '{plan.query_text}'")
            return []

        # Parallel retrieval execution across all active strategies
        tasks = [r.search(plan) for r in active_instances]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_candidates: List[RetrievedCandidateDTO] = []
        for r_list in results:
            if isinstance(r_list, list):
                all_candidates.extend(r_list)
            elif isinstance(r_list, Exception):
                logger.error(f"Retriever execution error: {r_list}")

        return all_candidates
