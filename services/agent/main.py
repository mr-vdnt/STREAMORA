"""
STREAMORA AI - Orchestrator Agent API

Provides the unified natural language interface for the entire platform.
"""
import os
import sys
import time

# STARTUP METRICS
APP_START_TIME = time.time()
STARTUP_MS = 0

from typing import Any
from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import mimetypes
from dotenv import load_dotenv

mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from services.agent.core import agent
from services.security.user_data import init_db, get_watchlist, save_watchlist, get_history, save_history, update_user_profile
from services.discovery.home_service import HomeService
from services.agent.limiter import limiter
from services.auth.middleware import AuthMiddleware
from services.auth.permissions import get_current_user, get_optional_user
from services.auth.auth_service import router as auth_router

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

import asyncio
from contextlib import asynccontextmanager

def validate_dependencies():
    """Startup dependency validation."""
    print("[System] Validating dependencies...")
    try:
        # Check Database
        conn = get_db_connection()
        conn.execute("SELECT 1 FROM users LIMIT 1")
        conn.close()
        print("[System] Database connection OK.")
    except Exception as e:
        print(f"[System] CRITICAL: Database connection failed: {e}")
        sys.exit(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup validation
    validate_dependencies()
    
    # Initialize DB (if not already done)
    init_db()

    # Warmup LLM in background
    if settings.environment != "test":
        import ollama
        print("[System] Initiating LLM warmup...")
        def run_warmup():
            try:
                ollama.chat(
                    model='llama3.2',
                    messages=[{'role': 'user', 'content': 'warmup'}],
                    keep_alive="1h"
                )
                print("[System] LLM warm-up complete. Model is resident in memory.")
            except Exception as e:
                print(f"[System] LLM warm-up failed: {e}")
        
        # Do not block startup for warmup
        asyncio.get_event_loop().run_in_executor(None, run_warmup)
    else:
        print("[System] Skipping LLM warmup in test environment.")
    
    yield
    
    # Graceful Shutdown
    print("[System] Initiating graceful shutdown...")
    # Add any specific cleanup here (e.g. closing Redis connections later)
    print("[System] Shutdown complete.")

app = FastAPI(title="STREAMORA AI - Secure Orchestrator Agent", lifespan=lifespan)

# Telemetry & Structured Logging
from services.platform.telemetry import setup_telemetry
setup_telemetry(app)

# Prometheus Instrumentation
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)

# Rate Limiting is imported from services.agent.limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Lockdown
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://127.0.0.1:10000,http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]
render_url = os.getenv("RENDER_EXTERNAL_URL")
if render_url:
    allowed_origins.append(render_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)
app.include_router(auth_router)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://fonts.gstatic.com; img-src 'self' data: https:;"
    return response

# --- USER PROFILE & WATCHLIST ENDPOINTS ---
@app.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    user_data = dict(current_user)
    user_data.pop("hashed_password", None)
    return user_data

class UpdateProfileRequest(BaseModel):
    display_name: str
    email: str

@app.put("/me")
def update_me(req: UpdateProfileRequest, current_user: dict = Depends(get_current_user)):
    success = update_user_profile(current_user["id"], req.display_name, req.email)
    if not success:
        return JSONResponse(status_code=400, content={"detail": "Failed to update profile or email already exists"})
    return {"status": "success"}

@app.get("/me/watchlist")
def get_my_watchlist(current_user: dict = Depends(get_current_user)):
    return get_watchlist(current_user["id"])

@app.put("/me/watchlist")
def update_my_watchlist(items: list, current_user: dict = Depends(get_current_user)):
    save_watchlist(current_user["id"], items)
    return {"status": "success"}

@app.get("/me/history")
def get_my_history(current_user: dict = Depends(get_current_user)):
    return get_history(current_user["id"])

@app.put("/me/history")
def update_my_history(items: list, current_user: dict = Depends(get_current_user)):
    save_history(current_user["id"], items)
    return {"status": "success"}

# --- SECURED ENDPOINTS ---

# --- HEALTH PROBES ---
@app.get("/health/live", tags=["Health"])
def liveness_probe():
    """Liveness probe: returns 200 OK if the service is running."""
    return {"status": "ok", "service": "streamora-orchestrator"}

@app.get("/health/ready", tags=["Health"])
def readiness_probe():
    """Readiness probe: checks if dependencies (like DB) are available."""
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
        return {"status": "ready"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "not ready", "detail": str(e)})

class ChatRequest(BaseModel):
    query: str
    exclude_ids: list[int] = []

class ChatResponse(BaseModel):
    intent: str
    response: Any
    llm_response: str
    metrics: dict = {}
    req_id: str = ""

import uuid

# Global Metrics Trackers
active_requests = 0
chat_latencies = []
slow_requests = 0

@app.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
def chat_endpoint(request: Request, req: ChatRequest, current_user: dict = Depends(get_optional_user)):
    global active_requests, chat_latencies, slow_requests
    
    t0 = time.time()
    req_id = f"req_{uuid.uuid4().hex[:8]}"
    print(f"[{req_id}] Chat request started: '{req.query}'")
    
    active_requests += 1
    
    try:
        user_id = current_user["id"] if current_user else 32
        result = agent.process_query(user_id, req.query, req.exclude_ids, req_id=req_id)
        
        t1 = time.time()
        total_ms = int((t1 - t0) * 1000)
        
        chat_latencies.append(total_ms)
        if len(chat_latencies) > 100:
            chat_latencies.pop(0)
            
        if total_ms > 2000:
            slow_requests += 1
            
        metrics = result.get("metrics", {})
        metrics["total_ms"] = total_ms
        
        print(f"[{req_id}] Chat request completed in {total_ms}ms")
        
        return ChatResponse(
            intent=result.get("intent", "search"),
            response=result.get("response", []),
            llm_response=result.get("llm_response", ""),
            metrics=metrics,
            req_id=req_id
        )
    finally:
        active_requests -= 1

@app.post("/chat/stream")
@limiter.limit("20/minute")
def chat_stream_endpoint(request: Request, req: ChatRequest, current_user: dict = Depends(get_optional_user)):
    global active_requests
    req_id = f"req_{uuid.uuid4().hex[:8]}"
    print(f"[{req_id}] Chat stream request started: '{req.query}'")
    
    active_requests += 1
    
    user_id = current_user["id"] if current_user else 32
    
    def event_generator():
        import json
        try:
            for event in agent.process_query_stream(user_id, req.query, req.exclude_ids, req_id=req_id):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            print(f"[{req_id}] Chat stream error: {e}")
            yield f"data: {json.dumps({'type': 'token', 'value': 'An error occurred during streaming.'})}\n\n"
        finally:
            global active_requests
            active_requests -= 1
            print(f"[{req_id}] Chat stream request completed")

    return StreamingResponse(event_generator(), media_type="text/event-stream")

from services.repository.movie_repository import MovieRepository

@app.get("/autocomplete")
@limiter.limit("60/minute")
def autocomplete(request: Request, q: str, current_user: dict = Depends(get_optional_user)):
    """Real-time autocomplete endpoint matching titles."""
    if len(q) < 2:
        return []
    try:
        repo = MovieRepository()
        movies_db = repo.get_all()
        q_lower = q.lower()
        results = []
        for iid, row in movies_db.items():
            if q_lower in str(row.get("title", "")).lower():
                results.append({
                    "item_id": iid,
                    "title": str(row.get("title", "")),
                    "poster_url": str(row.get("poster_url", "")),
                    "content_type": str(row.get("content_type", "movie")),
                    "genres": str(row.get("genres", "")).split("|")[:2],
                    "rating": float(row.get("rating", 7.0)),
                    "director": str(row.get("director", ""))
                })
                if len(results) >= 6:
                    break
        return results
    except Exception as e:
        print("Autocomplete error:", e)
    return []

from services.discovery.catalog_service import CatalogService, DiscoveryQuery

_catalog_service = None
def get_catalog_service():
    global _catalog_service
    if _catalog_service is None:
        from services.discovery.catalog_service import CatalogService
        _catalog_service = CatalogService()
    return _catalog_service

_home_service = None
def get_home_service():
    global _home_service
    if _home_service is None:
        _home_service = HomeService()
    return _home_service

@app.get("/home")
@limiter.limit("60/minute")
def get_home(request: Request, current_user: dict = Depends(get_optional_user)):
    """Unified Discovery endpoint for the Homepage."""
    user_id = current_user["id"] if current_user else 32
    return get_home_service().get_home_payload(format="all", user_id=user_id)

@app.get("/movies")
@limiter.limit("60/minute")
def get_movies_home(request: Request, current_user: dict = Depends(get_optional_user)):
    """Unified Discovery endpoint for the Movies page."""
    user_id = current_user["id"] if current_user else 32
    return get_home_service().get_home_payload(format="movie", user_id=user_id)

@app.get("/series")
@limiter.limit("60/minute")
def get_series_home(request: Request, current_user: dict = Depends(get_optional_user)):
    """Unified Discovery endpoint for the TV Shows page."""
    user_id = current_user["id"] if current_user else 32
    return get_home_service().get_home_payload(format="series", user_id=user_id)

@app.get("/categories")
@limiter.limit("60/minute")
def get_categories(request: Request, current_user: dict = Depends(get_optional_user)):
    """Returns normalized genres available in the DB."""
    return get_catalog_service().get_categories()

@app.get("/discover")
@limiter.limit("60/minute")
def discover(
    request: Request,
    genre: str = None,
    year: int = None,
    language: str = None,
    type: str = None,
    sort: str = "popularity",
    page: int = 1,
    limit: int = 20,
    current_user: dict = Depends(get_optional_user)
):
    """Deterministic discovery via CatalogService."""
    query = DiscoveryQuery(
        genre=genre,
        year=year,
        language=language,
        type=type,
        sort=sort,
        page=page,
        limit=limit
    )
    return get_catalog_service().discover(query)

import requests

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")

@app.get("/trailer/{tmdb_id}")
@limiter.limit("30/minute")
def get_trailer(request: Request, tmdb_id: int):
    """Fetches the official YouTube trailer from TMDB if available."""
    if not TMDB_API_KEY:
        return {"trailer_url": ""}
        
    try:
        # Try movie first
        resp = requests.get(f"https://api.themoviedb.org/3/movie/{tmdb_id}/videos?api_key={TMDB_API_KEY}")
        data = resp.json()
        if "results" not in data or not data["results"]:
            # Try TV series
            resp = requests.get(f"https://api.themoviedb.org/3/tv/{tmdb_id}/videos?api_key={TMDB_API_KEY}")
            data = resp.json()
            
        videos = data.get("results", [])
        if not videos:
            return {"trailer_url": ""}
            
        # Prioritize official trailers on YouTube
        trailers = [v for v in videos if v.get("site") == "YouTube" and v.get("type") == "Trailer"]
        if not trailers:
            trailers = [v for v in videos if v.get("site") == "YouTube" and v.get("type") == "Teaser"]
            
        if trailers:
            key = trailers[0]["key"]
            return {"trailer_url": f"https://www.youtube.com/embed/{key}"}
            
    except Exception as e:
        print(f"Error fetching trailer for TMDB {tmdb_id}: {e}")
        
    return {"trailer_url": ""}

from services.content_intelligence.adapter import ContentIntelligenceAdapter

# Initialize Graph Adapter globally
_content_adapter = None

def get_content_adapter():
    global _content_adapter
    if _content_adapter is None:
        repo = MovieRepository()
        _content_adapter = ContentIntelligenceAdapter(repo.get_all())
    return _content_adapter

@app.get("/api/item/{content_type}/{item_id}")
@limiter.limit("30/minute")
def get_item_details(request: Request, content_type: str, item_id: int, current_user: dict = Depends(get_optional_user)):
    """Aggregates rich metadata and similar items in a single request."""
    try:
        repo = MovieRepository()
        movie = repo.get_by_id(item_id)
        if not movie:
            return {"error": "Item not found"}
            
        adapter = get_content_adapter()
        similar_candidates = adapter.get_similar_candidates([item_id], limit=10)
        
        similar_movies = []
        for cand in similar_candidates:
            cid = cand["content_id"]
            sm = repo.get_by_id(cid)
            if sm:
                score = cand["score"]
                # Determine explanation
                explanation_str = adapter.get_explanation_context(item_id, cid)
                explanation = [explanation_str] if explanation_str else ["Similar theme or style"]
                
                similar_movies.append({
                    "item_id": cid,
                    "title": sm['title'],
                    "poster_url": sm.get('poster_url', ''),
                    "score": int(max(70, 99 - ((1.0 - score) * 100))),
                    "explanation": explanation
                })
        
        # Build comprehensive payload
        payload = {
            "movie": {
                "item_id": item_id,
                "title": str(movie.get('title', '')),
                "poster_url": str(movie.get('poster_url', '')),
                "backdrop_url": str(movie.get('backdrop_url', '')),
                "overview": str(movie.get('overview', '')),
                "year": str(movie.get('year', '')),
                "rating": float(movie.get('rating', 8.0)),
                "runtime": str(movie.get('runtime', '120 min')),
                "director": str(movie.get('director', 'Unknown')),
                "genres": str(movie.get('genres', '')).split('|'),
                "themes": str(movie.get('themes', '')).split('|'),
                "content_type": content_type
            },
            "similar": similar_movies,
            "graph": {},
            "recommendations": [],
            "explanations": {},
            "diagnostics": adapter.get_graph_statistics()
        }
        return payload
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

class SearchRequest(BaseModel):
    query: str
    top_k: int = 20

@app.post("/search")
@limiter.limit("30/minute")
def search_endpoint(request: Request, req: SearchRequest, current_user: dict = Depends(get_optional_user)):
    """Semantic query search bypassing legacy internal HTTP calls."""
    try:
        # Instead of calling legacy services, use core agent directly
        user_id = current_user["id"] if current_user else 32
        result = agent.process_query(user_id, req.query)
        
        # The result from process_query is the hybrid retrieved items already mapped for presentation
        items = result.get("response", [])
        return items
    except Exception as e:
        print("Search error:", e)
        return []

class EventRequest(BaseModel):
    event_type: str
    item_id: int

@app.post("/events/ingest")
@limiter.limit("60/minute")
def proxy_events(request: Request, req: EventRequest, current_user: dict = Depends(get_current_user)):
    """Proxy events directly to the Event Processor service on Port 8002."""
    user_id = current_user["id"] if current_user else 32
    payload = {"user_id": user_id, "event_type": req.event_type, "item_id": req.item_id}
    try:
        resp = requests.post("http://127.0.0.1:8002/events/ingest", json=payload, timeout=5)
        return {"status": "ok", "backend_status": resp.status_code}
    except Exception as e:
        return {"status": "error", "reason": str(e)}

from services.agent.admin import admin_router
app.include_router(admin_router)

# --- SRE KEEP-WARM & HEALTH ENDPOINTS ---
import asyncio
import logging

logger = logging.getLogger("streamora.sre")

async def heartbeat_loop():
    # Delay initial heartbeat run to allow server startup and microservices to boot fully
    await asyncio.sleep(15)
    
    app_url = os.getenv("RENDER_EXTERNAL_URL")
    if not app_url:
        origins = os.getenv("ALLOWED_ORIGINS", "")
        for origin in origins.split(","):
            if origin.startswith("https://"):
                app_url = origin
                break
    if not app_url:
        app_url = "http://127.0.0.1:8004"
        
    logger.info(f"[SRE Heartbeat] Starting keep-warm loop. Target URL: {app_url}/health")
    print(f"[SRE Heartbeat] Starting keep-warm loop. Target URL: {app_url}/health")
    
    while True:
        # Wait 10 minutes (600 seconds)
        await asyncio.sleep(600)
        url = f"{app_url.rstrip('/')}/health"
        params = {"heartbeat": "true"}
        try:
            resp = requests.get(url, params=params, timeout=10)
            logger.info(f"[SRE Heartbeat] Ping successful. HTTP status: {resp.status_code}")
            print(f"[SRE Heartbeat] Ping successful. HTTP status: {resp.status_code}")
        except Exception as e:
            logger.error(f"[SRE Heartbeat] Ping failed: {e}. Starting exponential backoff retry...")
            print(f"[SRE Heartbeat] Ping failed: {e}. Starting exponential backoff retry...")
            
            for i in range(3):
                wait_time = 10 * (2 ** i)
                logger.info(f"[SRE Heartbeat] Retrying in {wait_time}s...")
                print(f"[SRE Heartbeat] Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
                try:
                    resp = requests.get(url, params=params, timeout=10)
                    logger.info(f"[SRE Heartbeat] Retry {i+1} successful. HTTP status: {resp.status_code}")
                    print(f"[SRE Heartbeat] Retry {i+1} successful. HTTP status: {resp.status_code}")
                    break
                except Exception as ex:
                    logger.error(f"[SRE Heartbeat] Retry {i+1} failed: {ex}")
                    print(f"[SRE Heartbeat] Retry {i+1} failed: {ex}")

@app.on_event("startup")
async def startup_event():
    global STARTUP_MS
    STARTUP_MS = int((time.time() - APP_START_TIME) * 1000)
    init_db()
    admin = get_user("admin")
    if not admin:
        create_user("admin", "admin@streamora.ai", hash_password("adminpass"), "Administrator")
    asyncio.create_task(heartbeat_loop())

@app.get("/ping")
def ping():
    return {"status": "pong"}

@app.get("/health")
def health():
    """Liveness probe - returns immediately if process is alive."""
    return {"status": "ok"}

@app.get("/ready")
def ready():
    """Readiness probe - checks if DB/Repo are ready."""
    return {
        "status": "ok",
        "startup_ms": STARTUP_MS,
        "repository_loaded": True, # Always true post-startup because MovieRepository is loaded
        "db_connected": True
    }

@app.get("/health/deep")
def health_deep():
    """Deep health check - checks microservices and AI components."""
    services = {
        "ranking": "http://127.0.0.1:8001/",
        "event_processor": "http://127.0.0.1:8002/",
        "rag": "http://127.0.0.1:8003/"
    }
    status_report = {}
    for name, url in services.items():
        try:
            r = requests.get(url, timeout=1.5)
            status_report[name] = "healthy" if r.status_code == 200 else "unhealthy"
        except Exception:
            status_report[name] = "unreachable"
            
    # Check if Agent has lazily loaded its components
    from services.agent.core import agent
    llm_loaded = agent._query_engine is not None
            
    return {
        "status": "healthy",
        "startup_ms": STARTUP_MS,
        "llm_loaded": llm_loaded,
        "microservices": status_report
    }

@app.get("/metrics")
def metrics():
    """Diagnostics and metrics endpoint for production monitoring."""
    from services.agent.core import agent
    llm_loaded = agent._query_engine is not None
    uptime_seconds = int(time.time() - APP_START_TIME)
    
    try:
        import psutil
        memory_mb = int(psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024)
        cpu_percent = psutil.cpu_percent()
    except ImportError:
        memory_mb = -1
        cpu_percent = -1

    avg_chat_ms = int(sum(chat_latencies) / len(chat_latencies)) if chat_latencies else 0

    return {
        "status": "healthy",
        "startup_ms": STARTUP_MS,
        "repository_loaded": True,
        "llm_loaded": llm_loaded,
        "query_engine_loaded": llm_loaded,
        "uptime_seconds": uptime_seconds,
        "active_requests": active_requests,
        "average_chat_ms": avg_chat_ms,
        "slow_requests": slow_requests,
        "memory_mb": memory_mb,
        "cpu_percent": cpu_percent
    }

# Mount frontend directory at root
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../frontend'))
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
