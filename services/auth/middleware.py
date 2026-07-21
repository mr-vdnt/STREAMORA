import re
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from .jwt_service import verify_token
from .audit_logger import log_event
import uuid

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, public_paths=None, allowed_origins=None):
        super().__init__(app)
        # Paths that do not require authentication
        self.public_paths = public_paths or [
            r"^/$",
            r"^/health$",
            r"^/health/.*",
            r"^/metrics$",
            r"^/token$",
            r"^/register$",
            r"^/static/.*",
            r"^/favicon\.ico$",
            r"^/css/.*",
            r"^/js/.*",
            r"^/img/.*",
            r"^/assets/.*",
            r"^/.*\.css$",
            r"^/.*\.js$",
            r"^/modal/.*"
        ]
        import os
        origins_str = os.getenv("ALLOWED_ORIGINS", "http://127.0.0.1:10000,http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000")
        self.allowed_origins = [o.strip() for o in origins_str.split(",")]
        render_url = os.getenv("RENDER_EXTERNAL_URL")
        if render_url:
            self.allowed_origins.append(render_url.rstrip("/"))

    async def dispatch(self, request: Request, call_next):
        # CSRF Protection: Verify Origin for state-changing methods
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            origin = request.headers.get("origin")
            referer = request.headers.get("referer")
            
            # Allow if no origin/referer (e.g., direct API client), but block mismatched origins
            if origin and origin not in self.allowed_origins:
                return JSONResponse(status_code=403, content={"detail": "CSRF check failed: Invalid Origin"})
            if referer and not any(referer.startswith(o) for o in self.allowed_origins):
                return JSONResponse(status_code=403, content={"detail": "CSRF check failed: Invalid Referer"})

        # Check if the path is public
        is_public = any(re.match(pattern, request.url.path) for pattern in self.public_paths)
        
        req_id = str(uuid.uuid4())[:8]
        request.state.req_id = req_id
        client_ip = request.client.host if request.client else "unknown"
        request.state.client_ip = client_ip
        
        # We can extract token from HttpOnly cookie
        access_token = request.cookies.get("access_token")
        
        # Verify Token
        user_payload = None
        if access_token:
            user_payload = verify_token(access_token, token_type="access")
        
        request.state.user = user_payload
        
        # If route is NOT public and user is NOT authenticated, reject.
        if not is_public and not user_payload:
            log_event(
                who="Anonymous", 
                what="UNAUTHORIZED_ACCESS", 
                where=request.url.path, 
                details="No valid access token provided",
                ip=client_ip,
                req_id=req_id
            )
            return JSONResponse(status_code=401, content={"detail": "Not authenticated"})

        # Proceed to route
        response = await call_next(request)
        return response
