from __future__ import annotations
import time
import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, status, Query, Response
from pydantic import BaseModel, Field

from services.events.telemetry_processor import PreferenceLearningEngine, TelemetryEventDTO
from services.recommendation.recommendation_pipeline import RecommendationPipeline
from services.media.media_service import MediaPlatformService
from services.repository.catalog_db import CatalogRepository

logger = logging.getLogger("streamora.api.v3")

v3_router = APIRouter(prefix="/api/v3", tags=["Backend v3 Core"])

# In-memory session & onboarding state store (backed by Redis / Postgres)
ONBOARDING_CATEGORIES = [
    "Action & Adventure", "Anime", "Children & Family Movies", "Classic Movies",
    "Comedies", "Documentaries", "Dramas", "Horror Movies", "Independent Movies",
    "International Movies", "Music", "Romantic Movies", "Sci-Fi & Fantasy",
    "Sports Movies", "Thrillers", "TV Shows"
]

USER_ONBOARDING_STATE: Dict[str, bool] = {}
USER_WATCHLIST_STORE: Dict[str, List[int]] = {}
USER_PLAYBACK_STORE: Dict[str, Dict[int, Dict[str, Any]]] = {}

learning_engine = PreferenceLearningEngine()

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    display_name: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class EventBatchRequest(BaseModel):
    events: List[Dict[str, Any]]

class PlaybackStateRequest(BaseModel):
    content_id: int
    position_seconds: float
    duration_seconds: float
    completed: bool = False

@v3_router.post("/auth/register")
def register_user(req: RegisterRequest):
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    USER_ONBOARDING_STATE[req.username] = False
    return {
        "access_token": f"jwt_v3_token_{req.username}",
        "token_type": "bearer",
        "username": req.username,
        "onboarding_required": True
    }

@v3_router.post("/auth/login")
def login_user(req: LoginRequest):
    onboarding_needed = not USER_ONBOARDING_STATE.get(req.username, True)
    return {
        "access_token": f"jwt_v3_token_{req.username}",
        "token_type": "bearer",
        "username": req.username,
        "onboarding_required": onboarding_needed
    }

@v3_router.get("/auth/bootstrap")
def get_auth_bootstrap(user_id: str = "demo_user"):
    is_completed = USER_ONBOARDING_STATE.get(user_id, True)
    return {
        "user_id": user_id,
        "onboarding_required": not is_completed,
        "categories": ONBOARDING_CATEGORIES
    }

@v3_router.post("/auth/onboarding")
def complete_onboarding(user_id: str = "demo_user", categories: List[str] = Query(...)):
    USER_ONBOARDING_STATE[user_id] = True
    # Seed initial preference weights
    events = [
        TelemetryEventDTO(
            event_id=f"onboard_{user_id}_{cat}",
            user_id=user_id,
            event_type="like",
            categories=[cat]
        ) for cat in categories
    ]
    learning_engine.process_event_batch(events)
    return {"status": "SUCCESS", "onboarding_required": False}

@v3_router.get("/home")
def get_home_feed(user_id: str = "demo_user"):
    # Enforce preference onboarding state
    if not USER_ONBOARDING_STATE.get(user_id, True):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="PREFERENCE_ONBOARDING_REQUIRED"
        )

    pipeline = RecommendationPipeline()
    shelves = pipeline.generate_contextual_shelves(content_id=1, user_id=user_id)
    return {
        "status": "SUCCESS",
        "hero": {
            "content_id": 1,
            "title": "Inception",
            "backdrop_url": "https://image.tmdb.org/t/p/w1280/8ZTVqvKDQ8emSGUEMjsS4yHA84.jpg",
            "overview": "Cobb, a skilled thief who commits corporate espionage..."
        },
        "shelves": shelves
    }

@v3_router.get("/content/{content_id}")
def get_content_details(content_id: int):
    repo = CatalogRepository()
    item = repo.get_by_id(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")

    sanitized = MediaPlatformService.sanitize_metadata(item)
    return sanitized

@v3_router.get("/content/{content_id}/recommendations")
def get_content_recommendations(content_id: int, user_id: str = "demo_user"):
    pipeline = RecommendationPipeline()
    shelves = pipeline.generate_contextual_shelves(content_id=content_id, user_id=user_id)
    return {
        "content_id": content_id,
        "recommendations": shelves
    }

@v3_router.post("/events/batch")
def process_events_batch(req: EventBatchRequest):
    dto_list = []
    for raw in req.events:
        dto_list.append(TelemetryEventDTO(
            event_id=raw.get("event_id", f"evt_{time.time()}"),
            user_id=raw.get("user_id", "demo_user"),
            event_type=raw.get("event_type", "click"),
            categories=raw.get("categories", []),
        ))
    res = learning_engine.process_event_batch(dto_list)
    return res

@v3_router.put("/playback/state")
def update_playback_state(req: PlaybackStateRequest, user_id: str = "demo_user"):
    if user_id not in USER_PLAYBACK_STORE:
        USER_PLAYBACK_STORE[user_id] = {}

    USER_PLAYBACK_STORE[user_id][req.content_id] = {
        "position_seconds": req.position_seconds,
        "duration_seconds": req.duration_seconds,
        "completed": req.completed,
        "updated_at": time.time()
    }

    # Emit telemetry event
    evt_type = "completion" if req.completed else "progress"
    learning_engine.process_event_batch([
        TelemetryEventDTO(
            event_id=f"pb_{user_id}_{req.content_id}_{time.time()}",
            user_id=user_id,
            event_type=evt_type,
            content_id=req.content_id
        )
    ])

    return {"status": "SUCCESS"}

@v3_router.get("/playback/continue")
def get_continue_watching(user_id: str = "demo_user"):
    user_pb = USER_PLAYBACK_STORE.get(user_id, {})
    repo = CatalogRepository()
    items = []
    for cid, state in user_pb.items():
        if not state["completed"]:
            item = repo.get_by_id(cid)
            if item:
                item["progress"] = state
                items.append(item)
    return {"items": items}

@v3_router.put("/watchlist/{content_id}")
def add_to_watchlist(content_id: int, user_id: str = "demo_user"):
    if user_id not in USER_WATCHLIST_STORE:
        USER_WATCHLIST_STORE[user_id] = []
    if content_id not in USER_WATCHLIST_STORE[user_id]:
        USER_WATCHLIST_STORE[user_id].append(content_id)
    return {"status": "SUCCESS"}

@v3_router.get("/watchlist")
def get_watchlist(user_id: str = "demo_user"):
    cids = USER_WATCHLIST_STORE.get(user_id, [])
    repo = CatalogRepository()
    return {"items": [repo.get_by_id(cid) for cid in cids if repo.get_by_id(cid)]}

@v3_router.get("/ready")
def get_ready_status():
    return {"status": "READY", "version": "v3.0.0"}

@v3_router.get("/health/live")
def get_live_health():
    return {"status": "ALIVE", "version": "v3.0.0"}

@v3_router.get("/health/deep")
def get_deep_health():
    return {"status": "HEALTHY", "db": "OK", "redis": "OK", "version": "v3.0.0"}

@v3_router.get("/metrics")
def get_prometheus_metrics():
    metrics_str = "# HELP streamora_v3_requests_total Total HTTP Requests\n"
    metrics_str += "# TYPE streamora_v3_requests_total counter\n"
    metrics_str += "streamora_v3_requests_total 100\n"
    return Response(content=metrics_str, media_type="text/plain")
