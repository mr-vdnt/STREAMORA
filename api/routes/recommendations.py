from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Dict, Any, Optional

from services.platform.startup import container
from services.platform.context import RequestContext
from services.platform.logging.request_logger import log_request_trace
from services.platform.security.validation import validate_query, ValidationError
from services.platform.security.rate_limit import rate_limiter, RateLimitExceeded
from services.platform.resilience.circuit_breaker import circuit_breaker
from services.platform.monitoring.metrics import metrics_registry

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    user_id: Optional[str] = "anonymous"

@router.post("/")
@circuit_breaker(failure_threshold=5, recovery_timeout=30)
def get_recommendation(request: ChatRequest, x_session_id: Optional[str] = Header(None)) -> Dict[str, Any]:
    # 1. Validation & Rate Limiting
    try:
        sanitized_query = validate_query(request.query)
        rate_limiter.check_limit(request.user_id)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RateLimitExceeded as e:
        raise HTTPException(status_code=429, detail=str(e))
        
    # 2. Setup Context
    context = RequestContext(user_id=request.user_id, session_id=x_session_id)
    
    # 3. Execute Pipeline
    try:
        if not container.agent:
            raise HTTPException(status_code=503, detail="Agent not ready.")
            
        metrics_registry.increment("requests_total")
        
        # In a fully refactored system, the context would be passed down to capture timings.
        # For now, we wrap the agent call.
        response = container.agent.process_query(int(request.user_id) if request.user_id.isdigit() else 1, sanitized_query)
        
        # Simulated timing for trace purposes (in reality, components would record this into context)
        context.record_timing("pipeline", context.diagnostics["total_ms"])
        
    except Exception as e:
        metrics_registry.increment("requests_failed")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        context.finish()
        log_request_trace(context, endpoint="/recommendations/")
        
    return response
