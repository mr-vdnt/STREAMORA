from __future__ import annotations
from fastapi import APIRouter, Depends, Request
from services.search.dtos import SearchQueryDTO
from services.search.search_pipeline import SearchPlatformPipeline
from services.search.planner.planner import QueryPlanner
from services.search.autocomplete.autocomplete_engine import MultiEntityAutocompleteEngine
from services.repository.catalog_db import CatalogRepository, SearchEvent

search_router = APIRouter(prefix="/search", tags=["Search Platform"])

@search_router.get("/query")
async def execute_search_query(q: str, limit: int = 20, offset: int = 0):
    """
    Execute hybrid search via Query Planner, Optimizer, Retrieval Marketplace, Fusion, and LTR Ranker.
    """
    pipeline = SearchPlatformPipeline()
    query_dto = SearchQueryDTO(raw_query=q, limit=limit, offset=offset)
    return await pipeline.execute_search(query_dto)


@search_router.get("/plan")
def inspect_query_plan(q: str):
    """
    Inspect the generated SearchPlan for debugging and plan optimization.
    """
    planner = QueryPlanner()
    query_dto = SearchQueryDTO(raw_query=q)
    return planner.create_plan(query_dto)


@search_router.get("/suggest")
def autocomplete_suggestions(q: str):
    """
    Real-time multi-entity search-as-you-type autocomplete dropdown.
    """
    autocomplete_engine = MultiEntityAutocompleteEngine()
    return autocomplete_engine.autocomplete(q)


@search_router.get("/analytics")
def search_analytics_summary():
    """
    Retrieve search platform operational analytics (query counts, avg latency, recent events).
    """
    repo = CatalogRepository()
    with repo.get_session() as session:
        events = session.query(SearchEvent).order_by(SearchEvent.created_at.desc()).limit(20).all()
        total_queries = session.query(SearchEvent).count()

        event_logs = [
            {
                "id": e.id,
                "query": e.query_text,
                "intent": e.parsed_intent,
                "results_count": e.results_count,
                "latency_ms": e.latency_ms,
                "event_type": e.event_type,
                "created_at": e.created_at.isoformat() if e.created_at else None
            } for e in events
        ]

        return {
            "total_queries": total_queries,
            "recent_events": event_logs
        }
