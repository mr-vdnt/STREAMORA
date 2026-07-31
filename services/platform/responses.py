from typing import Generic, TypeVar, Optional, Any, Dict
from pydantic import BaseModel
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from services.platform.exceptions import ApplicationError
import time
import uuid

T = TypeVar("T")

class ResponseMeta(BaseModel):
    request_id: str
    timestamp: str
    execution_ms: float

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[Dict[str, Any]] = None
    meta: ResponseMeta

def make_success_response(data: Any, request: Request = None, execution_ms: float = 0.0) -> Dict[str, Any]:
    req_id = getattr(getattr(request, "state", None), "req_id", str(uuid.uuid4())[:8]) if request else str(uuid.uuid4())[:8]
    return {
        "success": True,
        "data": data,
        "error": None,
        "meta": {
            "request_id": req_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "execution_ms": round(execution_ms, 2)
        }
    }

def make_error_response(code: str, message: str, details: list = None, request: Request = None) -> Dict[str, Any]:
    req_id = getattr(getattr(request, "state", None), "req_id", str(uuid.uuid4())[:8]) if request else str(uuid.uuid4())[:8]
    return {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": details or []
        },
        "meta": {
            "request_id": req_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "execution_ms": 0.0
        }
    }

class GlobalExceptionMiddleware(BaseHTTPMiddleware):
    """
    Catches all uncaught exceptions and ApplicationErrors, returning standard error JSON responses.
    """
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        try:
            response = await call_next(request)
            return response
        except ApplicationError as app_err:
            return JSONResponse(
                status_code=app_err.status_code,
                content=make_error_response(app_err.code, app_err.message, app_err.details, request)
            )
        except Exception as exc:
            return JSONResponse(
                status_code=500,
                content=make_error_response("INTERNAL_SERVER_ERROR", str(exc), [], request)
            )
