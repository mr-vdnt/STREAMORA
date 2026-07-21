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

@v2_router.get("/item/{content_type}/{item_id}")
def get_item_v2(request: Request, content_type: str, item_id: int, current_user: dict = Depends(get_optional_user)):
    movie = get_catalog().get_by_id(item_id)
    if not movie:
        return {"error": "Item not found"}
        
    shelves = get_similarity().get_similar_items(item_id, top_k=15, multi_shelf=True)
    
    return {
        "movie": {
            "item_id": item_id,
            "title": str(movie.get('title', '')),
            "poster_url": str(movie.get('poster_url', '')),
            "backdrop_url": str(movie.get('backdrop_url', '')),
            "overview": str(movie.get('overview', '')),
            "year": str(movie.get('year', '')),
            "rating": float(movie.get('rating', 8.0) or 8.0),
            "runtime": str(movie.get('runtime', '120 min')),
            "director": str(movie.get('director', 'Unknown')),
            "genres": str(movie.get('genres', '')).split('|'),
            "themes": str(movie.get('themes', '')).split('|'),
            "content_type": content_type
        },
        "recommendations": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "engine_version": "v2",
            "shelves": shelves
        }
    }

@v2_router.post("/search")
def search_v2(request: Request, req: SearchRequest, current_user: dict = Depends(get_optional_user)):
    user_id = current_user["id"] if current_user else 32
    start_time = datetime.utcnow()
    
    result = get_agent().process_query(user_id, req.query)
    items = result.get("response", [])
    
    latency = (datetime.utcnow() - start_time).total_seconds()
    
    # Fire and forget analytics event
    from services.analytics.event_pipeline import EventPipeline
    EventPipeline.log_search({
        "event_type": "search",
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "query": req.query,
        "latency": latency,
        "results": len(items),
        "clicked_movie": None,
        "session_id": request.headers.get("x-session-id", "unknown"),
        "device": request.headers.get("user-agent", "unknown")
    })
    
    return items
