import json
from .logger import get_logger
from services.platform.context import RequestContext

logger = get_logger("streamora.request")

def log_request_trace(context: RequestContext, endpoint: str = "/recommend"):
    """Logs a structured trace of the request processing stages."""
    trace = {
        "request_id": context.request_id,
        "user_id": context.user_id,
        "session_id": context.session_id,
        "endpoint": endpoint,
        "latency_ms": context.diagnostics.get("total_ms", 0),
        "stages": context.diagnostics
    }
    
    # In production this prints valid JSON for log aggregators
    logger.info(json.dumps(trace))
