from __future__ import annotations
import hashlib
import json
from typing import Any, Dict
from services.search.planner.query_intelligence import QueryIntelligence
from services.search.dtos import SearchPlanDTO, SearchQueryDTO

class QueryPlanner:
    """
    Layer 2 Query Planner Engine.
    Transforms raw query input and query intelligence into an explicit, executable SearchPlanDTO.
    """

    def __init__(self):
        self.intelligence = QueryIntelligence()

    def create_plan(self, query_dto: SearchQueryDTO) -> SearchPlanDTO:
        qi = self.intelligence.process(query_dto.raw_query)

        active_retrievers = ["lexical"]
        intent = qi["intent"]

        if intent in ["theme_mood_query", "similarity_query", "generic_search"]:
            active_retrievers.append("knowledge_fact")
        if intent in ["similarity_query"]:
            active_retrievers.extend(["relationship", "embedding"])
        if intent in ["franchise_query"]:
            active_retrievers.extend(["franchise", "relationship"])

        # Compute deterministic plan hash
        plan_data = f"{qi['rewritten_query']}:{intent}:{sorted(active_retrievers)}"
        plan_hash = hashlib.sha256(plan_data.encode('utf-8')).hexdigest()[:16]

        return SearchPlanDTO(
            query_text=query_dto.raw_query,
            rewritten_query=qi["rewritten_query"],
            intent=intent,
            extracted_entities=qi["extracted_entities"],
            target_themes=qi["extracted_themes"],
            target_moods=qi["extracted_moods"],
            active_retrievers=active_retrievers,
            estimated_cost=len(active_retrievers) * 1.5,
            estimated_recall=0.92,
            latency_budget_ms=100.0,
            plan_hash=plan_hash
        )
