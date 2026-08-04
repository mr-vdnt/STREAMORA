from fastapi import APIRouter
from services.config.feature_flags import FeatureFlagPlatform
from services.config.runtime_config import RuntimeConfigService

config_router = APIRouter(prefix="/config", tags=["Configuration & Feature Flags"])
feature_flags = FeatureFlagPlatform()
runtime_config = RuntimeConfigService()

@config_router.get("/flags")
def get_feature_flags():
    return {"flags": feature_flags.get_all_flags()}

@config_router.get("/runtime")
def get_runtime_config():
    return {"config": runtime_config.get_all()}
