from fastapi import APIRouter
from services.discovery.discovery_service import DiscoveryPlatformService

discovery_router = APIRouter(prefix="/discovery", tags=["Discovery Platform"])
service = DiscoveryPlatformService()

@discovery_router.get("/collections")
def get_collections():
    cols = service.get_collections()
    return {"collections": [col.__dict__ for col in cols]}

@discovery_router.get("/hubs/{hub_slug}")
def get_hub(hub_slug: str):
    hub = service.get_hub(hub_slug)
    return hub.__dict__
