from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from services.recommendation.recommendation_pipeline import RecommendationPipeline
from services.recommendation.orchestrator.home_feed_orchestrator import HomeFeedOrchestrator
from services.recommendation.analytics.telemetry import FeedbackTelemetryLogger

recommendation_router = APIRouter(prefix="/recommendations", tags=["Recommendation Platform"])

class FeedbackRequest(BaseModel):
    user_id: str
    content_id: int
    event_type: str  # watch, click, rate, dismiss, watchlist
    weight: float = 1.0

@recommendation_router.get("")
async def get_recommendations(
    slate: str = "personalized_home", 
    user_id: str = "demo_user", 
    context_item_id: Optional[int] = None, 
    limit: int = 20
):
    """
    Generic slate-driven recommendation endpoint (home, because_you_watched, trending, continue_watching).
    """
    if slate == "home" or slate == "home_feed":
        orchestrator = HomeFeedOrchestrator()
        return await orchestrator.build_home_feed(user_id)

    pipeline = RecommendationPipeline()
    return await pipeline.generate_slate(user_id=user_id, slate_type=slate, context_item_id=context_item_id, limit=limit)


@recommendation_router.get("/personalized")
async def get_personalized_recommendations(user_id: str = "demo_user", limit: int = 20):
    """
    Retrieve top personalized recommendation slate for user.
    """
    pipeline = RecommendationPipeline()
    return await pipeline.generate_slate(user_id=user_id, slate_type="personalized_home", limit=limit)


@recommendation_router.get("/because_you_watched/{content_id}")
async def get_because_you_watched(content_id: int, user_id: str = "demo_user", limit: int = 15):
    """
    Retrieve contextual 'Because You Watched' recommendations for a content item.
    """
    pipeline = RecommendationPipeline()
    return await pipeline.generate_slate(user_id=user_id, slate_type="because_you_watched", context_item_id=content_id, limit=limit)


@recommendation_router.post("/feedback")
def log_user_feedback(req: FeedbackRequest):
    """
    Log explicit or implicit interaction telemetry feedback (watch, click, rate, dismiss, watchlist).
    """
    telemetry = FeedbackTelemetryLogger()
    event_id = telemetry.log_interaction(
        user_id=req.user_id,
        content_id=req.content_id,
        event_type=req.event_type,
        weight=req.weight
    )
    return {"status": "success", "event_id": event_id}
