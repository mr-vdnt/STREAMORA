from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from services.events.telemetry_processor import PreferenceLearningEngine, TelemetryEventDTO
from services.recommendation.precomputation_worker import PrecomputationWorker
from services.recommendation.recommendation_pipeline import RecommendationPipeline
from services.media.media_service import MediaPlatformService
from services.repository.catalog_db import CatalogRepository

logger = logging.getLogger("streamora.api.v3")

v3_router = APIRouter(prefix="/api/v3", tags=["Backend v3"])

ONBOARDING_CATEGORIES = [
    "Action & Adventure", "Anime", "Children & Family Movies", "Classic Movies",
    "Comedies", "Documentaries", "Dramas", "Horror Movies", "Independent Movies",
    "International Movies", "Music", "Romantic Movies", "Sci-Fi & Fantasy",
    "Sports Movies", "Thrillers", "TV Shows",
]

USER_ONBOARDING_STATE: Dict[str, bool] = {}
USER_WATCHLIST_STORE: Dict[str, List[int]] = {}
USER_PLAYBACK_STORE: Dict[str, Dict[int, Dict[str, Any]]] = {}
CONTENT_REC_CACHE: Dict[int, Dict[str, Any]] = {}

learning_engine = PreferenceLearningEngine()
recommendation_pipeline = RecommendationPipeline()
precomputation_worker = PrecomputationWorker(repo=CatalogRepository())


class RegisterRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    email: str
    password: str = Field(min_length=6, max_length=256)
    display_name: Optional[str] = Field(default=None, max_length=120)


class LoginRequest(BaseModel):
    username: str
    password: str


class EventBatchRequest(BaseModel):
    events: List[Dict[str, Any]] = Field(default_factory=list, max_length=100)


class PlaybackStateRequest(BaseModel):
    content_id: int
    position_seconds: float = Field(ge=0)
    duration_seconds: float = Field(gt=0)
    completed: bool = False


@v3_router.post("/auth/register")
def register_user(req: RegisterRequest):
    USER_ONBOARDING_STATE[req.username] = False
    return {
        "access_token": f"jwt_v3_token_{req.username}",
        "token_type": "bearer",
        "username": req.username,
        "onboarding_required": True,
    }


@v3_router.post("/auth/login")
def login_user(req: LoginRequest):
    onboarding_needed = not USER_ONBOARDING_STATE.get(req.username, True)
    return {
        "access_token": f"jwt_v3_token_{req.username}",
        "token_type": "bearer",
        "username": req.username,
        "onboarding_required": onboarding_needed,
    }


@v3_router.get("/auth/bootstrap")
def get_auth_bootstrap(user_id: str = "demo_user"):
    is_completed = USER_ONBOARDING_STATE.get(user_id, True)
    return {
        "user_id": user_id,
        "onboarding_required": not is_completed,
        "categories": ONBOARDING_CATEGORIES,
    }


@v3_router.post("/auth/onboarding")
def complete_onboarding(user_id: str = "demo_user", categories: List[str] = Query(...)):
    valid = set(ONBOARDING_CATEGORIES)
    selected = [category for category in categories if category in valid]
    USER_ONBOARDING_STATE[user_id] = True
    events = [
        TelemetryEventDTO(
            event_id=f"onboard_{user_id}_{category}",
            user_id=user_id,
            event_type="like",
            categories=[category],
        )
        for category in selected
    ]
    if events:
        learning_engine.process_event_batch(events)
    return {"status": "SUCCESS", "onboarding_required": False, "selected_categories": selected}


@v3_router.get("/home")
def get_home_feed(user_id: str = "demo_user", format: str = Query("all", pattern="^(all|movie|series)$")):
    """Fast home read model.

    IMPORTANT: never execute the full recommendation pipeline on the request path.
    A cache miss builds a bounded catalog snapshot only; richer recommendation work is
    an offline/background concern.
    """
    if not USER_ONBOARDING_STATE.get(user_id, True):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="PREFERENCE_ONBOARDING_REQUIRED",
        )

    cached = precomputation_worker.get_precomputed_home_slate(user_id, format)
    if cached:
        return cached

    return precomputation_worker.precompute_user_home_slate(user_id, format)


@v3_router.get("/content/{content_id}")
def get_content_details(content_id: int):
    repo = CatalogRepository()
    item = repo.get_by_id(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")
    return MediaPlatformService.sanitize_metadata(item)


@v3_router.get("/content/{content_id}/recommendations")
def get_content_recommendations(content_id: int, user_id: str = "demo_user"):
    cached = CONTENT_REC_CACHE.get(content_id)
    if cached:
        return cached

    # Keep the expensive contextual graph computation out of the home path. It is only
    # executed when the user explicitly opens a title's recommendation section.
    shelves = recommendation_pipeline.generate_contextual_shelves(
        content_id=content_id,
        user_id=user_id,
    )
    result = {"content_id": content_id, "recommendations": shelves}
    CONTENT_REC_CACHE[content_id] = result
    return result


@v3_router.post("/events/batch")
def process_events_batch(req: EventBatchRequest):
    dto_list: List[TelemetryEventDTO] = []
    for index, raw in enumerate(req.events):
        dto_list.append(
            TelemetryEventDTO(
                event_id=str(raw.get("event_id") or f"evt_{time.time_ns()}_{index}"),
                user_id=str(raw.get("user_id") or "demo_user"),
                event_type=str(raw.get("event_type") or "click"),
                content_id=raw.get("content_id"),
                categories=list(raw.get("categories") or []),
            )
        )
    return learning_engine.process_event_batch(dto_list)


@v3_router.put("/playback/state")
def update_playback_state(req: PlaybackStateRequest, user_id: str = "demo_user"):
    USER_PLAYBACK_STORE.setdefault(user_id, {})[req.content_id] = {
        "position_seconds": req.position_seconds,
        "duration_seconds": req.duration_seconds,
        "completed": req.completed,
        "updated_at": time.time(),
    }
    event_type = "completion" if req.completed else "progress"
    learning_engine.process_event_batch([
        TelemetryEventDTO(
            event_id=f"pb_{user_id}_{req.content_id}_{time.time_ns()}",
            user_id=user_id,
            event_type=event_type,
            content_id=req.content_id,
        )
    ])
    return {"status": "SUCCESS"}


@v3_router.get("/playback/continue")
def get_continue_watching(user_id: str = "demo_user"):
    user_pb = USER_PLAYBACK_STORE.get(user_id, {})
    repo = CatalogRepository()
    items = []
    for content_id, state in user_pb.items():
        if state["completed"]:
            continue
        item = repo.get_by_id(content_id)
        if item:
            item["progress"] = state
            items.append(item)
    return {"items": items}


@v3_router.put("/watchlist/{content_id}")
def add_to_watchlist(content_id: int, user_id: str = "demo_user"):
    USER_WATCHLIST_STORE.setdefault(user_id, [])
    if content_id not in USER_WATCHLIST_STORE[user_id]:
        USER_WATCHLIST_STORE[user_id].append(content_id)
    return {"status": "SUCCESS"}


@v3_router.get("/watchlist")
def get_watchlist(user_id: str = "demo_user"):
    repo = CatalogRepository()
    content_ids = USER_WATCHLIST_STORE.get(user_id, [])
    return {"items": [repo.get_by_id(cid) for cid in content_ids if repo.get_by_id(cid)]}


@v3_router.get("/ready")
def get_ready_status():
    return {"status": "READY", "version": "3.1.1", "home_mode": "bounded-read-model"}


@v3_router.get("/health/live")
def get_live_health():
    return {"status": "ALIVE", "version": "3.1.1"}


@v3_router.get("/health/deep")
def get_deep_health():
    return {"status": "HEALTHY", "db": "OK", "recommendation_path": "async", "version": "3.1.1"}


@v3_router.get("/metrics")
def get_prometheus_metrics():
    return Response(
        content=(
            "# HELP streamora_v3_requests_total Total HTTP Requests\n"
            "# TYPE streamora_v3_requests_total counter\n"
            "streamora_v3_requests_total 0\n"
        ),
        media_type="text/plain",
    )
