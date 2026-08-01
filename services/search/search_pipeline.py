from __future__ import annotations
import time
import logging
from typing import List
from services.repository.catalog_db import CatalogRepository
from services.search.planner.planner import QueryPlanner
from services.search.optimizer.cost_optimizer import CostBasedQueryOptimizer
from services.search.retrievers.marketplace import RetrievalMarketplace
from services.search.retrievers.lexical import LexicalRetriever
from services.search.retrievers.knowledge import KnowledgeFactRetriever
from services.search.retrievers.relationship import RelationshipRetriever
from services.search.retrievers.franchise import FranchiseRetriever
from services.search.retrievers.embedding import EmbeddingRetriever
from services.search.fusion.candidate_fusion import CandidateFusionEngine
from services.search.ranking.heuristics import HeuristicRanker
from services.search.explainability.explainability import SearchExplainabilityGenerator
from services.search.analytics.search_telemetry import SearchTelemetryLogger
from services.search.dtos import (
    SearchQueryDTO, SearchResponseDTO, SearchResultItemDTO, SearchPlanDTO
)

logger = logging.getLogger("streamora.search.pipeline")

class SearchPlatformPipeline:
    """
    Master Search Platform Orchestrator.
    Executes: Query Intelligence -> Query Planner -> Cost-Based Query Optimizer -> Retrieval Marketplace -> Candidate Fusion -> Feature Store Ranking -> Search Explainability -> Telemetry Logger.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()
        self.planner = QueryPlanner()
        self.optimizer = CostBasedQueryOptimizer()
        self.fusion = CandidateFusionEngine()
        self.ranker = HeuristicRanker()
        self.explainer = SearchExplainabilityGenerator()
        self.telemetry = SearchTelemetryLogger(self.repo)

        # Initialize and register retrieval marketplace plugins
        self.marketplace = RetrievalMarketplace()
        self.marketplace.register(LexicalRetriever(self.repo))
        self.marketplace.register(KnowledgeFactRetriever(self.repo))
        self.marketplace.register(RelationshipRetriever(self.repo))
        self.marketplace.register(FranchiseRetriever(self.repo))
        self.marketplace.register(EmbeddingRetriever(self.repo))

    async def execute_search(self, query_dto: SearchQueryDTO) -> SearchResponseDTO:
        start_time = time.time()

        # 1. Query Planning
        raw_plan = self.planner.create_plan(query_dto)

        # 2. Cost-Based Query Optimization
        optimized_plan = self.optimizer.optimize_plan(raw_plan)

        # 3. Parallel Candidate Retrieval via Marketplace
        raw_candidates = await self.marketplace.execute_retrieval(optimized_plan)

        # 4. Strategy-Aware Candidate Fusion with Provenance
        fused_candidates = self.fusion.fuse_candidates(raw_candidates)

        # 5. Multi-Stage Feature Store Ranking Pipeline
        ranked_pairs = self.ranker.rank(fused_candidates, optimized_plan)

        # Apply Pagination (limit/offset)
        offset = query_dto.offset
        limit = query_dto.limit
        paged_pairs = ranked_pairs[offset:offset + limit]

        # 6. Search Explainability & Response Assembly
        results: List[SearchResultItemDTO] = []
        with self.repo.get_session() as session:
            for candidate, fv in paged_pairs:
                c_item = self.repo.get_by_id(candidate.content_id)
                if not c_item:
                    continue

                explanations = self.explainer.generate_explanations(candidate, fv, optimized_plan)
                sources = candidate.provenance_metadata.get("sources", [])

                results.append(SearchResultItemDTO(
                    content_id=c_item["id"],
                    title=c_item["title"],
                    slug=c_item["slug"],
                    entity_type=c_item["entity_type"],
                    poster_url=c_item["poster_url"],
                    backdrop_url=c_item["backdrop_url"],
                    rating=c_item["rating"],
                    popularity=c_item["popularity"],
                    rank_score=fv.final_rank_score,
                    matched_sources=sources,
                    explanations=explanations
                ))

        elapsed_ms = (time.time() - start_time) * 1000.0

        # 7. Log Telemetry Event
        self.telemetry.log_query_event(
            query_text=query_dto.raw_query,
            rewritten_query=optimized_plan.rewritten_query,
            intent=optimized_plan.intent,
            plan_hash=optimized_plan.plan_hash,
            results_count=len(results),
            latency_ms=elapsed_ms
        )

        return SearchResponseDTO(
            query_text=query_dto.raw_query,
            intent=optimized_plan.intent,
            plan_hash=optimized_plan.plan_hash,
            total_hits=len(ranked_pairs),
            latency_ms=round(elapsed_ms, 2),
            results=results
        )
