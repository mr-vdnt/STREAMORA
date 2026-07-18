from fastapi import APIRouter
from typing import Dict, Any
from services.platform.startup import container
from services.platform.monitoring.metrics import metrics_registry

router = APIRouter()

@router.get("/")
def get_health() -> Dict[str, Any]:
    if not container.health_check:
        return {"status": "starting"}
    return container.health_check.check()

@router.get("/ready")
def get_ready() -> Dict[str, str]:
    if container.health_check and container.health_check.check()["status"] == "ok":
        return {"status": "ready"}
    return {"status": "not_ready"}
    
@router.get("/live")
def get_live() -> Dict[str, str]:
    return {"status": "alive"}

@router.get("/metrics")
def get_metrics() -> Dict[str, Any]:
    cache_metrics = container.cache_manager.get_metrics() if container.cache_manager else {}
    return {
        "cache": cache_metrics,
        "application": metrics_registry.get_snapshot()
    }
