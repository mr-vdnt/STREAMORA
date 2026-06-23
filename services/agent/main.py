"""
AURORA AI - Orchestrator Agent API

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
from services.security.auth import get_current_user, create_access_token, verify_password, get_user, FAKE_DB, ACCESS_TOKEN_EXPIRE_MINUTES, timedelta, save_users_db, pwd_context
from services.security.audit import log_event

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

app = FastAPI(title="AURORA AI - Secure Orchestrator Agent")

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
    response.headers["Content-Security-Policy"] = "default-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com; img-src 'self' data: https:;"
    return response

# --- AUTHENTICATION ---
class SignupRequest(BaseModel):
    username: str
    password: str

@app.post("/signup")
@limiter.limit("5/minute")
async def signup_endpoint(request: Request, req: SignupRequest):
    username = req.username.strip()
    # If signing up with email, restrict to Gmail
    if "@" in username:
        if not username.lower().endswith("@gmail.com"):
            return JSONResponse(
                status_code=400,
                content={"detail": "Sign up via email is restricted to Gmail (@gmail.com) addresses."}
            )
    
    # Check if user already exists
    if get_user(username):
        return JSONResponse(
            status_code=400,
            content={"detail": "Username or Gmail address is already registered."}
        )
    
    # Register the user
    new_uid = len(FAKE_DB) + 32
    FAKE_DB[username] = {
        "user_id": new_uid,
        "username": username,
        "hashed_password": pwd_context.hash(req.password),
        "role": "Standard"
    }
    save_users_db()
    log_event(who=username, what="USER_SIGNED_UP", where="/signup", details=f"Assigned ID: {new_uid}")
    return {"status": "success", "message": "User registered successfully"}

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
            matches = df[df['title'].str.contains(q, case=False, na=False)].head(5)
            titles = matches['title'].tolist()
            titles = [t.split(" (")[0] for t in titles]
            return titles
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

# Mount frontend directory at root
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../frontend'))
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
