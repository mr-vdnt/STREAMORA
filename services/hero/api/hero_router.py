from fastapi import APIRouter, Query
from services.hero.hero_service import HeroIntelligencePlatform

hero_router = APIRouter(prefix="/hero", tags=["Hero Intelligence"])
platform = HeroIntelligencePlatform()

@hero_router.get("/banner")
def get_hero_banner(user_id: str = Query("guest")):
    return platform.get_hero_banner(user_id=user_id)
