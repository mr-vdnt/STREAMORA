from fastapi import APIRouter, Query
from services.media.media_service import MediaPlatformService

media_router = APIRouter(prefix="/media", tags=["Media & CDN Platform"])
service = MediaPlatformService()

@media_router.get("/bundle/{content_id}")
def get_media_bundle(
    content_id: int,
    backdrop_path: str = Query(None),
    poster_path: str = Query(None)
):
    return service.get_full_media_bundle(content_id, backdrop_path, poster_path)

@media_router.get("/signed_url/{content_id}")
def get_signed_url(content_id: int, quality: str = Query("1080p")):
    url = service.stream_resolver.generate_signed_stream_url(content_id, quality)
    return {"content_id": content_id, "quality": quality, "signed_url": url}
