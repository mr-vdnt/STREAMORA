"""
STREAMORA AI - Orchestrator Agent API

Provides the unified natural language interface for the entire platform.
"""
import os
import sys
from typing import Any
from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
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
from services.security.auth import get_current_user, create_access_token, verify_password, get_user, FAKE_DB, ACCESS_TOKEN_EXPIRE_MINUTES, timedelta
from services.security.audit import log_event

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

app = FastAPI(title="STREAMORA AI - Secure Orchestrator Agent")

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Lockdown
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://127.0.0.1:10000")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://fonts.gstatic.com; img-src 'self' data: https:;"
    return response

# --- AUTHENTICATION ---
@app.post("/token")
@limiter.limit("10/minute")
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        log_event(who=form_data.username, what="LOGIN_FAILED", where="/token", details="Invalid credentials")
        return JSONResponse(status_code=401, content={"detail": "Incorrect username or password"})
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"], "user_id": user["user_id"]},
        expires_delta=access_token_expires
    )
    log_event(who=user["username"], what="LOGIN_SUCCESS", where="/token", details=f"Role: {user['role']}")
    return {"access_token": access_token, "token_type": "bearer", "user_id": user["user_id"], "role": user["role"]}

# --- SECURED ENDPOINTS ---
class ChatRequest(BaseModel):
    query: str
    exclude_ids: list[int] = []

class ChatResponse(BaseModel):
    intent: str
    response: Any

@app.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
def chat_endpoint(request: Request, req: ChatRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    result = agent.process_query(user_id, req.query, req.exclude_ids)
    return ChatResponse(
        intent=result["intent"],
        response=result["response"]
    )

import pandas as pd
@app.get("/autocomplete")
@limiter.limit("60/minute")
def autocomplete(request: Request, q: str, current_user: dict = Depends(get_current_user)):
    """Real-time autocomplete endpoint matching movie titles."""
    if len(q) < 2:
        return []
    try:
        if os.path.exists("data/raw/movies.csv"):
            df = pd.read_csv("data/raw/movies.csv")
            matches = df[df['title'].str.contains(q, case=False, na=False)].head(6)
            results = []
            for _, row in matches.iterrows():
                results.append({
                    "item_id": int(row["item_id"]),
                    "title": str(row["title"]),
                    "poster_url": str(row.get("poster_url", "")),
                    "content_type": str(row.get("content_type", "movie")),
                    "genres": str(row.get("genres", "")).split("|")[:2],
                    "rating": float(row.get("rating", 7.0)),
                    "director": str(row.get("director", ""))
                })
            return results
    except Exception as e:
        print("Autocomplete error:", e)
    return []

import requests
@app.get("/movie/{item_id}")
@limiter.limit("30/minute")
def get_movie_details(request: Request, item_id: int, current_user: dict = Depends(get_current_user)):
    """Aggregates all 19 fields of rich metadata and similar movies for the Cinematic Modal."""
    user_id = current_user["user_id"]
    try:
        rag_resp = requests.post("http://127.0.0.1:8003/explain", json={"user_id": user_id, "item_id": item_id}, timeout=10)
        metadata = {}
        if rag_resp.status_code == 200:
            metadata = rag_resp.json().get("rich_metadata", {})
        
        sim_resp = requests.post("http://127.0.0.1:8001/similar", json={"item_id": item_id, "top_k": 10}, timeout=10)
        similar_movies = []
        if sim_resp.status_code == 200:
            similar_items = sim_resp.json()
            if os.path.exists("data/raw/movies.csv"):
                df = pd.read_csv("data/raw/movies.csv")
                for sim in similar_items:
                    sid = sim["item_id"]
                    sm_row = df[df['item_id'] == sid]
                    if not sm_row.empty:
                        sm = sm_row.iloc[0]
                        similar_movies.append({
                            "item_id": sid,
                            "title": sm['title'],
                            "poster_url": sm.get('poster_url', ''),
                            "score": int(max(70, 99 - (sim.get('retrieval_score', 0) * 10)))
                        })
                        
        metadata["similar_movies"] = similar_movies
        return metadata
    except Exception as e:
        return {"error": str(e)}

class SearchRequest(BaseModel):
    query: str
    top_k: int = 20

@app.post("/search")
@limiter.limit("30/minute")
def search_endpoint(request: Request, req: SearchRequest, current_user: dict = Depends(get_current_user)):
    """Semantic query search utilizing SentenceTransformer + FAISS."""
    try:
        resp = requests.post("http://127.0.0.1:8001/search", json={"query": req.query, "top_k": req.top_k}, timeout=10)
        if resp.status_code == 200:
            similar_items = resp.json()
            results = []
            if os.path.exists("data/raw/movies.csv"):
                df = pd.read_csv("data/raw/movies.csv")
                for sim in similar_items:
                    sid = sim["item_id"]
                    row = df[df['item_id'] == sid]
                    if not row.empty:
                        r = row.iloc[0]
                        results.append({
                            "item_id": sid,
                            "title": str(r['title']),
                            "poster_url": str(r.get('poster_url', '')),
                            "backdrop_url": str(r.get('backdrop_url', '')),
                            "overview": str(r.get('overview', '')),
                            "rich_metadata": {
                                "title": str(r['title']),
                                "year": str(r.get('year', '2024')),
                                "match_percentage": int(max(70, 99 - (sim.get('retrieval_score', 0) * 10))),
                                "rating": float(r.get('rating', 8.0)),
                                "runtime": str(r.get('runtime', '120 min')),
                                "director": str(r.get('director', 'Unknown Director')),
                                "genres": str(r.get('genres', '')).split('|'),
                                "themes": str(r.get('themes', '')).split('|'),
                                "moods": str(r.get('moods', '')).split('|')
                            }
                        })
            return results
        return {"error": f"Ranking API returned {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}

class EventRequest(BaseModel):
    event_type: str
    item_id: int

@app.post("/events/ingest")
@limiter.limit("60/minute")
def proxy_events(request: Request, req: EventRequest, current_user: dict = Depends(get_current_user)):
    """Proxy events directly to the Event Processor service on Port 8002."""
    user_id = current_user["user_id"]
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
    asyncio.create_task(heartbeat_loop())

@app.get("/ping")
def ping():
    return {"status": "pong"}

@app.get("/health")
def health():
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
            
    return {
        "status": "healthy",
        "microservices": status_report
    }

# Mount frontend directory at root
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../frontend'))
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
