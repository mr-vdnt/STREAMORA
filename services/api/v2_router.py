from fastapi import APIRouter, Request, Depends
from typing import Dict, Any
from datetime import datetime

from services.auth.permissions import get_optional_user
from services.discovery.home_service import HomeService
from services.repository.catalog_db import CatalogRepository
from services.recommendation.similarity_engine import SimilarityEngine
from services.recommendation.explanation_engine import ExplanationEngine
from services.agent.core import OrchestratorAgent
from pydantic import BaseModel

v2_router = APIRouter(prefix="/api/v2")

class SearchRequest(BaseModel):
    query: str

_home_service = None
_catalog_repo = None
_similarity_engine = None
_explanation_engine = None
_agent = None

def get_home_service():
    global _home_service
    if _home_service is None:
        _home_service = HomeService()
    return _home_service

def get_catalog():
    global _catalog_repo
    if _catalog_repo is None:
        _catalog_repo = CatalogRepository()
    return _catalog_repo
    
def get_similarity():
    global _similarity_engine
    if _similarity_engine is None:
        _similarity_engine = SimilarityEngine()
    return _similarity_engine
    
def get_explanation():
    global _explanation_engine
    if _explanation_engine is None:
        _explanation_engine = ExplanationEngine()
    return _explanation_engine

def get_agent():
    global _agent
    if _agent is None:
        _agent = OrchestratorAgent()
    return _agent


@v2_router.get("/home")
def get_home_v2(request: Request, format: str = "all", current_user: dict = Depends(get_optional_user)):
    user_id = current_user["id"] if current_user else 32
    payload = get_home_service().get_home_payload(format=format, user_id=user_id)
    
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "cache_age": 120,
        "algorithm_version": "2.0",
        "hero": payload.get("hero", {}),
        "sections": payload.get("sections", [])
    }

@v2_router.get("/genre/{genre}")
def get_genre_v2(request: Request, genre: str, current_user: dict = Depends(get_optional_user)):
    user_id = current_user["id"] if current_user else 32
    payload = get_home_service().get_genre_payload(genre=genre, user_id=user_id)
    
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "cache_age": 120,
        "algorithm_version": "2.0",
        "metadata": payload.get("metadata", {}),
        "hero": payload.get("hero", {}),
        "sections": payload.get("sections", [])
    }

@v2_router.get("/content/{identifier}")
async def get_content_by_slug_or_uuid(request: Request, identifier: str, current_user: dict = Depends(get_optional_user)):
    from services.repository.movie_repository import MovieRepository
    from services.repository.series_repository import SeriesRepository

    movie_repo = MovieRepository()
    series_repo = SeriesRepository()

    # Try slug or UUID lookup for movie
    movie = movie_repo.find_by_slug(identifier) or movie_repo.find_by_uuid(identifier)
    if movie:
        from services.discovery.movie_orchestrator import MovieDetailOrchestrator
        return await MovieDetailOrchestrator().get_movie_detail(movie["id"])

    # Try slug or UUID lookup for series
    series = series_repo.find_by_slug(identifier) or series_repo.find_by_uuid(identifier)
    if series:
        from services.discovery.series_orchestrator import SeriesDetailOrchestrator
        return await SeriesDetailOrchestrator().get_series_detail(series["id"])

    return {"error": f"Content not found for identifier: {identifier}"}


# ── Catalog Operations & Intelligence Dashboards ──────────────────────

@v2_router.get("/catalog/health")
def get_catalog_health(request: Request):
    from services.catalog.catalog_health import CatalogHealthService
    return CatalogHealthService().audit_catalog_health()

@v2_router.get("/catalog/duplicates")
def get_catalog_duplicates(request: Request):
    return {"status": "ok", "duplicates": []}

@v2_router.get("/catalog/missing")
def get_catalog_missing_metadata(request: Request):
    from services.catalog.catalog_health import CatalogHealthService
    report = CatalogHealthService().audit_catalog_health()
    return {"status": "ok", "missing_metrics": report.get("metrics", {})}

@v2_router.get("/catalog/statistics")
def get_catalog_statistics(request: Request):
    from services.catalog.catalog_health import CatalogHealthService
    report = CatalogHealthService().audit_catalog_health()
    return {
        "total_items": report.get("total_items", 0),
        "health_score": report.get("health_score", 100.0),
        "status": report.get("status", "Healthy")
    }


# ── RC2.6: Search Intelligence Endpoints ──────────────────────────────

@v2_router.get("/autocomplete")
def autocomplete_v2(request: Request, q: str = "", current_user: dict = Depends(get_optional_user)):
    """
    Rich real-time autocomplete with entity-type classification.
    Returns grouped results: titles, genres, directors, actors.
    Designed for the frontend search-as-you-type dropdown.
    """
    if len(q) < 2:
        return {"titles": [], "genres": [], "directors": [], "actors": []}

    from services.repository.movie_repository import MovieRepository
    import unicodedata

    def norm(text: str) -> str:
        text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
        return text.lower().strip()

    q_norm = norm(q)
    movies_db = MovieRepository().get_all()

    titles = []
    genres_seen: set = set()
    directors_seen: set = set()
    actors_seen: set = set()

    for iid, row in movies_db.items():
        title = str(row.get('title', ''))
        title_norm = norm(title)
        poster = str(row.get('poster_url', ''))
        content_type = str(row.get('content_type', 'movie'))
        year = str(row.get('year', ''))
        rating = float(row.get('rating', 0) or 0)
        genre_list = [g.strip() for g in str(row.get('genres', '')).split('|') if g.strip()]

        # Title match (prefix preferred, then substring)
        if q_norm in title_norm:
            if poster:  # only include if poster exists
                titles.append({
                    "item_id": iid,
                    "title": title,
                    "poster_url": poster,
                    "content_type": content_type,
                    "genres": genre_list[:2],
                    "year": year,
                    "rating": round(rating, 1),
                    # Boost prefix matches for ranking
                    "_score": 2 if title_norm.startswith(q_norm) else 1
                })

        # Genre extraction
        for g in genre_list:
            g_norm = norm(g)
            if q_norm in g_norm and g not in genres_seen:
                genres_seen.add(g)

        # Director extraction
        director = str(row.get('director', ''))
        for d in director.split(','):
            d = d.strip()
            if d and q_norm in norm(d) and d not in directors_seen:
                directors_seen.add(d)

        # Actor extraction
        cast = str(row.get('cast', ''))
        for a in cast.split(','):
            a = a.strip()
            if a and q_norm in norm(a) and a not in actors_seen:
                actors_seen.add(a)

    # Sort & truncate titles by score then rating
    titles.sort(key=lambda x: (-x["_score"], -x["rating"]))
    for t in titles:
        t.pop("_score", None)
    titles = titles[:8]

    genres = sorted(list(genres_seen))[:5]
    directors = sorted(list(directors_seen))[:5]
    actors = sorted(list(actors_seen))[:5]

    return {
        "titles": titles,
        "genres": genres,
        "directors": directors,
        "actors": actors
    }


@v2_router.get("/search/instant")
def instant_search_v2(
    request: Request,
    q: str = "",
    limit: int = 24,
    content_type: str = "all",
    current_user: dict = Depends(get_optional_user)
):
    """
    Fast keyword search — no AI pipeline, no vector index.
    Searches title, genres, director, cast, overview with scoring.
    Used for the immediate grid render on the search page.
    """
    if not q or len(q) < 2:
        return {"results": [], "total": 0, "query": q, "engine": "instant"}

    from services.catalog.search import DeterministicSearchEngine
    from services.repository.movie_repository import MovieRepository

    movies_db = MovieRepository().get_all()
    engine = DeterministicSearchEngine(movies_db)
    raw = engine.search(q, limit=limit * 2)  # over-fetch for type filtering

    # Apply content_type filter
    if content_type != "all":
        raw = [r for r in raw if str(r.get('content_type', 'movie')).lower() == content_type.lower()]

    results = raw[:limit]
    return {
        "results": results,
        "total": len(results),
        "query": q,
        "engine": "instant"
    }


@v2_router.get("/search/intent")
def parse_intent_v2(request: Request, q: str = "", current_user: dict = Depends(get_optional_user)):
    """
    Exposes the NLP QueryIntelligenceEngine parse result.
    Used by the frontend to show the intent badge and parsed entities.
    """
    if not q:
        return {"intent": "search", "entities": {}, "query_plan": "deterministic_search"}

    from services.repository.movie_repository import MovieRepository
    from services.agent.query_intelligence import QueryIntelligenceEngine

    movies_db = MovieRepository().get_all()
    engine = QueryIntelligenceEngine(movies_db)
    result = engine.parse(q)
    return result
