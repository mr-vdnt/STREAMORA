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
            r"^/csrf-token$",
            r"^/auth/refresh$",
            r"^/auth/guest$",
            r"^/logout$",
            r"^/api/auth/register$",
            r"^/api/auth/login$",
            r"^/api/auth/token$",
            r"^/api/auth/refresh$",
            r"^/api/auth/csrf-token$",
            r"^/static/.*",
            r"^/favicon\.ico$",
            r"^/css/.*",
            r"^/js/.*",
            r"^/img/.*",
            r"^/assets/.*",
            r"^/.*\.css$",
            r"^/.*\.js$",
            r"^/modal/.*",
            r"^/api/v2/home.*$",
            r"^/api/v2/item/.*$",
            r"^/api/v2/content/.*$",
            r"^/api/v2/media-package/.*$",
            r"^/api/v2/person/.*$",
            r"^/api/v2/demo/system.*$",
            r"^/api/v2/genre/.*$",
            r"^/api/v2/search/.*$",
            r"^/api/v2/autocomplete.*$",
            r"^/home$",
            r"^/movies$",
            r"^/series$",
            r"^/categories$",
            r"^/search$"
        ]
        import os
        origins_str = os.getenv("ALLOWED_ORIGINS", "http://127.0.0.1:10000,http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000")
        self.allowed_origins = [o.strip() for o in origins_str.split(",")]
        render_url = os.getenv("RENDER_EXTERNAL_URL")
        if render_url:
            self.allowed_origins.append(render_url.rstrip("/"))

    async def dispatch(self, request: Request, call_next):
        # CSRF Protection: Verify X-CSRF-Token matches csrf_token cookie for state-changing methods
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            # Bypass CSRF checks for auth creation endpoints (match actual mounted paths)
            CSRF_EXEMPT = {
                "/token", "/register", "/auth/guest", "/logout", "/auth/refresh", # legacy bare paths
                "/api/auth/register", "/api/auth/login",   # actual mounted paths
                "/api/auth/token",                         # OAuth token endpoint
                "/search", "/api/v2/search",               # Search query endpoints
            }

            if request.url.path in CSRF_EXEMPT or request.url.path.startswith("/api/v2/search"):
                pass
            else:
                csrf_cookie = request.cookies.get("csrf_token")
                csrf_header = request.headers.get("x-csrf-token")
                
                # Check Origin/Referer as defense-in-depth
                origin = request.headers.get("origin")
                referer = request.headers.get("referer")
                if origin and origin not in self.allowed_origins:
                    return JSONResponse(status_code=403, content={"detail": "CSRF check failed: Invalid Origin"})
                if referer and not any(referer.startswith(o) for o in self.allowed_origins):
                    return JSONResponse(status_code=403, content={"detail": "CSRF check failed: Invalid Referer"})
                
                # Primary CSRF check: Double Submit Cookie
                if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
                    log_event("Unknown", "CSRF_FAILED", request.url.path, "CSRF token missing or mismatch", request.client.host if request.client else "unknown", "N/A")
                    return JSONResponse(status_code=403, content={"detail": "CSRF verification failed"})

        # Check if the path is public
        is_public = any(re.match(pattern, request.url.path) for pattern in self.public_paths)
        
        req_id = str(uuid.uuid4())[:8]
        request.state.req_id = req_id
        client_ip = request.client.host if request.client else "unknown"
        request.state.client_ip = client_ip
        
        # Extract token from Authorization header (Bearer token) or HttpOnly cookie
        access_token = request.cookies.get("access_token")
        auth_header = request.headers.get("authorization")
        if not access_token and auth_header and auth_header.startswith("Bearer "):
            access_token = auth_header.split(" ", 1)[1].strip()
        
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
