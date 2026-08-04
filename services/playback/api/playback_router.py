from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from services.playback.playback_service import PlaybackService
from services.auth.jwt_auth import get_current_user_account

playback_router = APIRouter(prefix="/playback", tags=["Playback & Streaming"])
service = PlaybackService()

class ProgressSyncRequest(BaseModel):
    content_id: int
    progress_seconds: float
    duration_seconds: float
    profile_id: Optional[int] = None

@playback_router.get("/manifest/{content_id}")
def get_stream_manifest(content_id: int, quality: str = Query("1080p")):
    return service.get_stream_manifest(content_id, quality)

@playback_router.post("/progress")
def sync_progress(req: ProgressSyncRequest, user: dict = Depends(get_current_user_account)):
    account_id = user.get("id", 1)
    return service.sync_watch_progress(
        account_id=account_id,
        content_id=req.content_id,
        progress_seconds=req.progress_seconds,
        duration_seconds=req.duration_seconds,
        profile_id=req.profile_id
    )

@playback_router.get("/continue_watching")
def get_continue_watching(user: dict = Depends(get_current_user_account)):
    account_id = user.get("id", 1)
    items = service.get_continue_watching(account_id)
    return {"items": items}
