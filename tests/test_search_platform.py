from __future__ import annotations
import asyncio
import pytest
from services.repository.catalog_db import CatalogRepository, SearchEvent
from services.search.dtos import SearchQueryDTO
from services.search.planner.query_intelligence import QueryIntelligence
from services.search.planner.planner import QueryPlanner
from services.search.optimizer.cost_optimizer import CostBasedQueryOptimizer
from services.search.fusion.candidate_fusion import CandidateFusionEngine
from services.search.search_pipeline import SearchPlatformPipeline
from services.search.autocomplete.autocomplete_engine import MultiEntityAutocompleteEngine
from services.search.evaluation.metrics import SearchEvaluator

@pytest.fixture
def catalog_repo():
    return CatalogRepository()

def test_query_intelligence_understanding():
    qi = QueryIntelligence()
    res = qi.process("funny sci-fi space movies like inception")

    assert res["intent"] in ["similarity_query", "theme_mood_query"]
    assert res["entity_type_filter"] == "movie"
    assert "space" in res["extracted_themes"]
    assert "funny" in res["extracted_moods"]

def test_query_planner_and_cost_optimizer():
    planner = QueryPlanner()
    optimizer = CostBasedQueryOptimizer()

    query_dto = SearchQueryDTO(raw_query="Inception")
    plan = planner.create_plan(query_dto)
    assert plan.intent == "exact_title"

    opt_plan = optimizer.optimize_plan(plan)
    assert "lexical" in opt_plan.active_retrievers

def test_candidate_fusion_provenance():
    fusion = CandidateFusionEngine()
    from services.search.dtos import RetrievedCandidateDTO

    c1 = RetrievedCandidateDTO(content_id=1, retriever_name="lexical", score=0.9, retrieval_reason="Lexical title match")
    c2 = RetrievedCandidateDTO(content_id=1, retriever_name="knowledge_fact", score=0.8, retrieval_reason="Theme match")

    fused = fusion.fuse_candidates([c1, c2])
    assert len(fused) == 1
    assert fused[0].content_id == 1
    assert "lexical" in fused[0].provenance_metadata["sources"]
    assert "knowledge_fact" in fused[0].provenance_metadata["sources"]

def test_autocomplete_dropdown():
    engine = MultiEntityAutocompleteEngine()
    res = engine.autocomplete("inc")

    assert res is not None
    assert res.query == "inc"

def test_search_evaluation_metrics():
    evaluator = SearchEvaluator()
    mrr = evaluator.compute_mrr([2, 5, 8])
    assert mrr == 1.0 / 3.0

    p_at_10 = evaluator.compute_precision_at_k([0, 1, 2], k=10)
    assert p_at_10 == 0.3

    ndcg = evaluator.compute_ndcg_at_k([1.0, 0.8, 0.6], k=3)
    assert ndcg > 0.0

def test_search_platform_pipeline_e2e(catalog_repo):
    pipeline = SearchPlatformPipeline(repo=catalog_repo)
    query_dto = SearchQueryDTO(raw_query="Inception")

    response = asyncio.run(pipeline.execute_search(query_dto))
    assert response is not None
    assert response.query_text == "Inception"
    assert response.latency_ms > 0.0
    assert len(response.results) > 0

    first_hit = response.results[0]
    assert first_hit.content_id == 1
    assert len(first_hit.explanations) > 0

    # Verify telemetry log in database
    with catalog_repo.get_session() as session:
        events = session.query(SearchEvent).filter(SearchEvent.query_text == "Inception").all()
        assert len(events) > 0
