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

from services.search.api.search_router import search_router
from services.recommendation.api.recommendation_router import recommendation_router
from services.auth.api.auth_router import auth_router
from services.discovery.api.discovery_router import discovery_router
from services.hero.api.hero_router import hero_router
from services.playback.api.playback_router import playback_router
from services.media.api.media_router import media_router
from services.notification.api.notification_router import notification_router
from services.admin.api.admin_router import admin_router
from services.observability.api.observability_router import observability_router
from services.config.api.config_router import config_router
from services.workers.api.workers_router import workers_router
from services.feature_store.api.feature_store_router import feature_store_router

v2_router.include_router(search_router)
v2_router.include_router(recommendation_router)
v2_router.include_router(auth_router)
v2_router.include_router(discovery_router)
v2_router.include_router(hero_router)
v2_router.include_router(playback_router)
v2_router.include_router(media_router)
v2_router.include_router(notification_router)
v2_router.include_router(admin_router)
v2_router.include_router(observability_router)
v2_router.include_router(config_router)
v2_router.include_router(workers_router)
v2_router.include_router(feature_store_router)

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
    from services.discovery.movie_orchestrator import MovieDetailOrchestrator
    from services.discovery.series_orchestrator import SeriesDetailOrchestrator

    movie_repo = MovieRepository()
    series_repo = SeriesRepository()

    # Try numeric ID lookup
    if identifier.isdigit():
        item_id = int(identifier)
        try:
            return await MovieDetailOrchestrator().get_movie_detail(item_id)
        except Exception:
            pass
        try:
            return await SeriesDetailOrchestrator().get_series_detail(item_id)
        except Exception:
            pass

    # Try slug or UUID lookup for movie
    movie = movie_repo.find_by_slug(identifier) or movie_repo.find_by_uuid(identifier)
    if movie:
        return await MovieDetailOrchestrator().get_movie_detail(movie["id"])

    # Try slug or UUID lookup for series
    series = series_repo.find_by_slug(identifier) or series_repo.find_by_uuid(identifier)
    if series:
        return await SeriesDetailOrchestrator().get_series_detail(series["id"])

    return {"error": f"Content not found for identifier: {identifier}"}

@v2_router.get("/media-package/{content_id}")
def get_media_package_endpoint(content_id: int, content_type: str = "movie", current_user: dict = Depends(get_optional_user)):
    from services.media_engine.media_package_service import MediaPackageService
    service = MediaPackageService()
    return service.get_media_package(content_id, content_type=content_type)

@v2_router.get("/media-package/{content_type}/{content_id}")
def get_typed_media_package_endpoint(content_type: str, content_id: int, current_user: dict = Depends(get_optional_user)):
    from services.media_engine.media_package_service import MediaPackageService
    service = MediaPackageService()
    return service.get_media_package(content_id, content_type=content_type)


@v2_router.get("/content/movie/{identifier}")
async def get_movie_content_endpoint(identifier: str, request: Request, current_user: dict = Depends(get_optional_user)):
    from services.repository.movie_repository import MovieRepository
    from services.discovery.movie_orchestrator import MovieDetailOrchestrator

    movie_repo = MovieRepository()
    if identifier.isdigit():
        res = await MovieDetailOrchestrator().get_movie_detail(int(identifier))
        if res:
            return res
        return {"error": f"Movie not found for ID: {identifier}"}

    movie = movie_repo.find_by_slug(identifier) or movie_repo.find_by_uuid(identifier)
    if movie:
        res = await MovieDetailOrchestrator().get_movie_detail(movie["id"])
        if res:
            return res

    return {"error": f"Movie not found for identifier: {identifier}"}

@v2_router.get("/content/series/{identifier}")
async def get_series_content_endpoint(identifier: str, request: Request, current_user: dict = Depends(get_optional_user)):
    from services.repository.series_repository import SeriesRepository
    from services.discovery.series_orchestrator import SeriesDetailOrchestrator

    series_repo = SeriesRepository()
    if identifier.isdigit():
        res = await SeriesDetailOrchestrator().get_series_detail(int(identifier))
        if res:
            return res
        return {"error": f"Series not found for ID: {identifier}"}

    series = series_repo.find_by_slug(identifier) or series_repo.find_by_uuid(identifier)
    if series:
        res = await SeriesDetailOrchestrator().get_series_detail(series["id"])
        if res:
            return res

    return {"error": f"Series not found for identifier: {identifier}"}


@v2_router.get("/content/series/{identifier}/season/{season_number}")
async def get_season_content_endpoint(identifier: str, season_number: int, request: Request, current_user: dict = Depends(get_optional_user)):
    from services.repository.series_repository import SeriesRepository
    series_repo = SeriesRepository()
    
    series_id = int(identifier) if identifier.isdigit() else None
    if not series_id:
        s = series_repo.find_by_slug(identifier) or series_repo.find_by_uuid(identifier)
        if s:
            series_id = s["id"]
            
    if not series_id:
        return {"error": f"Series not found for identifier: {identifier}"}

    series_data = series_repo.get_by_id(series_id)
    if not series_data:
        return {"error": "Series not found"}

    for season in series_data.get("seasons", []):
        if season.get("season_number") == season_number:
            return {
                "series_id": series_id,
                "series_title": series_data.get("title"),
                "season": season
            }

    return {"error": f"Season {season_number} not found for series {identifier}"}

@v2_router.get("/content/series/{identifier}/season/{season_number}/episode/{episode_number}")
async def get_episode_content_endpoint(identifier: str, season_number: int, episode_number: int, request: Request, current_user: dict = Depends(get_optional_user)):
    from services.repository.series_repository import SeriesRepository
    series_repo = SeriesRepository()

    series_id = int(identifier) if identifier.isdigit() else None
    if not series_id:
        s = series_repo.find_by_slug(identifier) or series_repo.find_by_uuid(identifier)
        if s:
            series_id = s["id"]

    if not series_id:
        return {"error": f"Series not found for identifier: {identifier}"}

    series_data = series_repo.get_by_id(series_id)
    if not series_data:
        return {"error": "Series not found"}

    for season in series_data.get("seasons", []):
        if season.get("season_number") == season_number:
            for ep in season.get("episodes", []):
                if ep.get("episode_number") == episode_number:
                    return {
                        "series_id": series_id,
                        "series_title": series_data.get("title"),
                        "season_number": season_number,
                        "episode": ep
                    }

    return {"error": f"Episode S{season_number}E{episode_number} not found for series {identifier}"}



@v2_router.get("/item/{content_type}/{item_id}")
async def get_item_details_v2(request: Request, content_type: str, item_id: str, current_user: dict = Depends(get_optional_user)):
    """
    Primary modal & detail overlay content endpoint used by frontend app.js.
    Supports movies & series by numeric ID, slug, or UUID.
    """
    from services.discovery.movie_orchestrator import MovieDetailOrchestrator
    from services.discovery.series_orchestrator import SeriesDetailOrchestrator

    normalized_type = str(content_type).lower().strip()

    if normalized_type in ("movie", "movies"):
        if item_id.isdigit():
            return await MovieDetailOrchestrator().get_movie_detail(int(item_id))
        else:
            return await get_content_by_slug_or_uuid(request, item_id, current_user)
    elif normalized_type in ("series", "tvseries", "tv"):
        if item_id.isdigit():
            return await SeriesDetailOrchestrator().get_series_detail(int(item_id))
        else:
            return await get_content_by_slug_or_uuid(request, item_id, current_user)

    # Generic fallback if content_type is unknown or 'all'
    if item_id.isdigit():
        num_id = int(item_id)
        try:
            return await MovieDetailOrchestrator().get_movie_detail(num_id)
        except Exception:
            return await SeriesDetailOrchestrator().get_series_detail(num_id)

    return await get_content_by_slug_or_uuid(request, item_id, current_user)


# ── Knowledge & Intelligence Platform (KIP) Endpoints ────────────────

@v2_router.post("/knowledge/extract/{content_id}")
async def extract_and_infer_knowledge(content_id: int, request: Request, current_user: dict = Depends(get_optional_user)):
    """
    Trigger baseline fact extraction & full inference engine pipeline for a content item.
    """
    from services.knowledge.pipeline import KnowledgePipeline
    pipeline = KnowledgePipeline()
    try:
        profile = await pipeline.process_content(content_id)
        return {
            "status": "success",
            "content_id": content_id,
            "fact_count": profile.fact_count,
            "overall_confidence": profile.overall_confidence,
            "profile": profile
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@v2_router.get("/knowledge/facts/{content_id}")
def get_knowledge_facts(content_id: int, request: Request, current_user: dict = Depends(get_optional_user)):
    """
    Retrieve all atomic facts, source reliability weights, confidence scores, and states for a content item.
    """
    from services.repository.catalog_db import CatalogRepository, KnowledgeFact
    repo = CatalogRepository()
    with repo.get_session() as session:
        facts = session.query(KnowledgeFact).filter(
            KnowledgeFact.content_id == content_id,
            KnowledgeFact.state == "ACTIVE"
        ).all()
        return {
            "content_id": content_id,
            "fact_count": len(facts),
            "facts": [
                {
                    "id": f.id,
                    "uuid": f.uuid,
                    "category": f.category,
                    "predicate": f.predicate,
                    "value": f.value,
                    "confidence": f.confidence,
                    "source_weight": f.source_weight,
                    "state": f.state,
                    "source_provider": f.source_provider,
                    "inference_model": f.inference_model,
                    "model_version": f.model_version
                } for f in facts
            ]
        }


@v2_router.get("/knowledge/profile/{content_id}")
def get_intelligence_profile(content_id: int, request: Request, current_user: dict = Depends(get_optional_user)):
    """
    Retrieve the materialized IntelligenceProfile CQRS read view for a content item.
    """
    import json
    from services.repository.catalog_db import CatalogRepository, IntelligenceProfile
    repo = CatalogRepository()
    with repo.get_session() as session:
        profile = session.query(IntelligenceProfile).filter(IntelligenceProfile.content_id == content_id).first()
        if not profile:
            return {"error": f"Intelligence profile not found for content_id {content_id}. Run /knowledge/extract/{content_id} first."}
        
        return {
            "content_id": profile.content_id,
            "snapshot_id": profile.snapshot_id,
            "profile_version": profile.profile_version,
            "dominant_themes": json.loads(profile.dominant_themes_json) if profile.dominant_themes_json else [],
            "dominant_moods": json.loads(profile.dominant_moods_json) if profile.dominant_moods_json else [],
            "pacing": profile.pacing,
            "narrative_structure": profile.narrative_structure,
            "audience_rating": profile.audience_rating,
            "content_warnings": json.loads(profile.content_warnings_json) if profile.content_warnings_json else [],
            "summaries": {
                "short": profile.summary_short,
                "medium": profile.summary_medium,
                "deep": profile.summary_deep,
                "spoiler_free": profile.summary_spoiler_free
            },
            "overall_confidence": profile.overall_confidence,
            "fact_count": profile.fact_count,
            "generated_at": profile.generated_at.isoformat() if profile.generated_at else None
        }


@v2_router.get("/knowledge/franchise/{slug}")
def get_franchise_universe(slug: str, request: Request, current_user: dict = Depends(get_optional_user)):
    """
    Retrieve franchise universe details, timeline ordering, and member contents.
    """
    from services.repository.catalog_db import CatalogRepository, FranchiseUniverse, FranchiseMember, Content
    repo = CatalogRepository()
    with repo.get_session() as session:
        franchise = session.query(FranchiseUniverse).filter(FranchiseUniverse.slug == slug).first()
        if not franchise:
            return {"error": f"Franchise universe not found for slug: {slug}"}

        members = session.query(FranchiseMember).filter(FranchiseMember.franchise_id == franchise.id).order_by(FranchiseMember.chronological_order).all()
        member_list = []
        for m in members:
            content = session.query(Content).filter(Content.id == m.content_id).first()
            meta = content.metadata_rel if content else None
            member_list.append({
                "content_id": m.content_id,
                "title": meta.title if meta else "Unknown",
                "chronological_order": m.chronological_order,
                "release_order": m.release_order,
                "timeline_era": m.timeline_era
            })

        return {
            "id": franchise.id,
            "uuid": franchise.uuid,
            "name": franchise.name,
            "slug": franchise.slug,
            "description": franchise.description,
            "backdrop_url": franchise.backdrop_url,
            "member_count": len(member_list),
            "members": member_list
        }


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

@v2_router.get("/person/{name}")

def get_person_profile(name: str, request: Request, current_user: dict = Depends(get_optional_user)):
    from services.repository.movie_repository import MovieRepository
    from services.repository.series_repository import SeriesRepository
    
    movie_repo = MovieRepository()
    series_repo = SeriesRepository()
    
    person_name = name.replace("-", " ").title()
    matched_movies = []
    
    for m in movie_repo.get_all().values():
        cast_str = str(m.get("cast", ""))
        director_str = str(m.get("director", ""))
        if person_name.lower() in cast_str.lower() or person_name.lower() in director_str.lower():
            matched_movies.append({
                "id": m.get("id"),
                "title": m.get("title"),
                "poster_url": m.get("poster_url"),
                "rating": m.get("rating"),
                "role": "Director" if person_name.lower() in director_str.lower() else "Actor"
            })
            
    return {
        "name": person_name,
        "biography": f"{person_name} is a renowned cinematic artist known for compelling storytelling and performances across major Streamora titles.",
        "avatar_url": f"https://ui-avatars.com/api/?name={person_name.replace(' ', '+')}&background=0D8ABC&color=fff",
        "known_for_count": len(matched_movies),
        "filmography": matched_movies
    }

@v2_router.get("/autocomplete")
def autocomplete_v2(request: Request, q: str = "", current_user: dict = Depends(get_optional_user)):
    """
    Rich real-time autocomplete with entity-type classification.
    Returns grouped results: titles, genres, directors, actors.
    Designed for the frontend search-as-you-type dropdown.
    """
    if not q or len(q) < 2:
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

@v2_router.get("/demo/system")
def get_demo_system_metrics(request: Request, current_user: dict = Depends(get_optional_user)):
    """
    Operational demo system metrics endpoint powering the Admin Dashboard.
    """
    from services.analytics.system_service import SystemAnalyticsService
    service = SystemAnalyticsService()
    return service.get_system_metrics()



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


# ─────────────────────────────────────────────────────────────
# DAP Ingestion Management Endpoints
# ─────────────────────────────────────────────────────────────

@v2_router.post("/ingestion/sync/{connector_name}")
async def trigger_ingestion_sync(
    connector_name: str,
    entity_type: str = "movie",
    limit: int = 20,
    current_user: dict = Depends(get_optional_user)
):
    """Trigger an on-demand sync run for a connector (e.g. tmdb)."""
    from services.ingestion.scheduler import IngestionScheduler
    from services.ingestion.connectors.tmdb_connector import TMDBConnector

    scheduler = IngestionScheduler()
    if connector_name == "tmdb":
        scheduler.register_connector(TMDBConnector())

    report = await scheduler.trigger_sync(connector_name, entity_type=entity_type, limit=limit)
    return {
        "job_id": report.job_id,
        "connector": report.connector_name,
        "items_fetched": report.items_fetched,
        "items_created": report.items_created,
        "items_updated": report.items_updated,
        "items_skipped": report.items_skipped,
        "items_failed": report.items_failed,
        "error_summary": report.error_summary,
    }


@v2_router.get("/ingestion/jobs")
def list_ingestion_jobs(limit: int = 10, current_user: dict = Depends(get_optional_user)):
    """List recent ingestion job runs."""
    from services.repository.catalog_db import CatalogRepository, IngestionJob

    repo = CatalogRepository()
    with repo.get_session() as session:
        jobs = session.query(IngestionJob).order_by(IngestionJob.created_at.desc()).limit(limit).all()
        return [
            {
                "id": j.id,
                "uuid": j.uuid,
                "connector_name": j.connector_name,
                "job_type": j.job_type,
                "status": j.status,
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "completed_at": j.completed_at.isoformat() if j.completed_at else None,
                "items_fetched": j.items_fetched,
                "items_ingested": j.items_ingested,
                "items_skipped": j.items_skipped,
                "items_failed": j.items_failed,
                "error_summary": j.error_summary,
            }
            for j in jobs
        ]


@v2_router.get("/ingestion/dead-letters")
def list_dead_letters(limit: int = 20, current_user: dict = Depends(get_optional_user)):
    """List items in the dead-letter queue requiring manual inspection."""
    from services.repository.catalog_db import CatalogRepository, DeadLetterRecord

    repo = CatalogRepository()
    with repo.get_session() as session:
        records = session.query(DeadLetterRecord).filter(
            DeadLetterRecord.is_resolved == False
        ).order_by(DeadLetterRecord.created_at.desc()).limit(limit).all()

        return [
            {
                "id": r.id,
                "job_id": r.job_id,
                "connector_name": r.connector_name,
                "external_id": r.external_id,
                "failure_stage": r.failure_stage,
                "failure_reason": r.failure_reason,
                "retry_count": r.retry_count,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ]


@v2_router.post("/ingestion/dead-letters/{record_id}/retry")
async def retry_dead_letter(record_id: int, current_user: dict = Depends(get_optional_user)):
    """Re-queue and retry a dead-letter payload."""
    import json
    from services.repository.catalog_db import CatalogRepository, DeadLetterRecord
    from services.ingestion.pipeline import DataAcquisitionPipeline
    from services.ingestion.dtos import RawPayloadDTO

    repo = CatalogRepository()
    with repo.get_session() as session:
        dlr = session.query(DeadLetterRecord).filter(DeadLetterRecord.id == record_id).first()
        if not dlr:
            return {"error": f"Dead letter record #{record_id} not found"}, 404

        raw_data = json.loads(dlr.payload_json) if dlr.payload_json else {}
        dto = RawPayloadDTO(
            connector_name=dlr.connector_name,
            external_id=dlr.external_id,
            entity_type="movie",
            raw_data=raw_data,
        )

        pipeline = DataAcquisitionPipeline(repo)
        result = await pipeline.process_raw_payload(dto, job_id=dlr.job_id)

        if result.success:
            dlr.is_resolved = True
            session.commit()
            return {"status": "retried_successfully", "result": result.action, "content_id": result.content_id}
        else:
            dlr.retry_count += 1
            session.commit()
            return {"status": "retry_failed", "errors": result.errors}
