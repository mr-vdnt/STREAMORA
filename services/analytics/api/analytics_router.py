from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any
from services.analytics.analytics_service import ProductAnalyticsEngine

analytics_router = APIRouter(prefix="/analytics", tags=["Product Analytics Engine"])
engine = ProductAnalyticsEngine()

class TrackEventRequest(BaseModel):
    event_name: str
    user_id: str
    content_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

@analytics_router.get("/dashboard")
def get_dashboard_metrics():
    return engine.get_dashboard_metrics()

@analytics_router.post("/track")
def track_event(req: TrackEventRequest):
    return engine.track_event(
        event_name=req.event_name,
        user_id=req.user_id,
        content_id=req.content_id,
        metadata=req.metadata
    )
