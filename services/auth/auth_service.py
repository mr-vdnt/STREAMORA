from fastapi import APIRouter, Depends, Request, Response, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import time

from .password_service import verify_password, hash_password, DUMMY_HASH
from .jwt_service import create_access_token, create_refresh_token, verify_token
from .cookie_service import set_auth_cookies, clear_auth_cookies
from .audit_logger import log_event
from .validators import validate_password, validate_username, validate_email
from services.security.user_data import get_user_by_username, create_user
from services.agent.limiter import limiter

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    display_name: Optional[str] = None

@router.post("/token")
@limiter.limit("10/minute")
async def login(request: Request, response: Response, payload: LoginRequest):
    req_id = getattr(request.state, "req_id", "N/A")
    ip = getattr(request.state, "client_ip", "unknown")
    
    # We delay response slightly for unknown users using constant time verify
    user = get_user_by_username(payload.username)
    if not user:
        verify_password(payload.password, DUMMY_HASH)
        log_event(who=payload.username, what="LOGIN_FAILED", where="/token", details="Invalid credentials", ip=ip, req_id=req_id)
        raise HTTPException(status_code=401, detail="Invalid username or password.")
        
    if not verify_password(payload.password, user["hashed_password"]):
        log_event(who=payload.username, what="LOGIN_FAILED", where="/token", details="Invalid credentials", ip=ip, req_id=req_id)
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    # Generate tokens
    user_data = {"sub": user["username"], "role": user["role"], "user_id": user["id"]}
    access_token = create_access_token(data=user_data)
    refresh_token = create_refresh_token(data=user_data)

    set_auth_cookies(response, access_token, refresh_token)
    
    log_event(who=user["username"], what="LOGIN_SUCCESS", where="/token", details=f"Role: {user['role']}", ip=ip, req_id=req_id)
    
    return {
        "status": "success",
        "user_id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "display_name": user["display_name"],
        "email": user["email"]
    }

@router.post("/register")
@limiter.limit("5/minute")
async def register(request: Request, payload: RegisterRequest):
    req_id = getattr(request.state, "req_id", "N/A")
    ip = getattr(request.state, "client_ip", "unknown")
    
    if not validate_username(payload.username):
        raise HTTPException(status_code=400, detail="Invalid username format")
    if not validate_email(payload.email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    if not validate_password(payload.password):
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    user_id = create_user(
        payload.username, 
        payload.email, 
        hash_password(payload.password), 
        payload.display_name or payload.username
    )
    
    if not user_id:
        log_event(who=payload.username, what="REGISTER_FAILED", where="/register", details="Username or email exists", ip=ip, req_id=req_id)
        raise HTTPException(status_code=400, detail="Username or email already registered")

    log_event(who=payload.username, what="REGISTER_SUCCESS", where="/register", details=f"User ID: {user_id}", ip=ip, req_id=req_id)
    return {"status": "success"}

@router.post("/auth/refresh")
@limiter.limit("5/minute")
async def refresh_token(request: Request, response: Response):
    req_id = getattr(request.state, "req_id", "N/A")
    ip = getattr(request.state, "client_ip", "unknown")
    
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token provided")
        
    payload = verify_token(refresh_token, token_type="refresh")
    if not payload:
        log_event(who="Unknown", what="REFRESH_FAILED", where="/auth/refresh", details="Invalid refresh token", ip=ip, req_id=req_id)
        raise HTTPException(status_code=401, detail="Invalid refresh token")
        
    username = payload.get("sub")
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
        
    # Generate new tokens (Rotation)
    user_data = {"sub": user["username"], "role": user["role"], "user_id": user["id"]}
    new_access_token = create_access_token(data=user_data)
    new_refresh_token = create_refresh_token(data=user_data)
    
    set_auth_cookies(response, new_access_token, new_refresh_token)
    log_event(who=username, what="REFRESH_SUCCESS", where="/auth/refresh", details="", ip=ip, req_id=req_id)
    
    return {"status": "success"}

@router.post("/logout")
@limiter.limit("10/minute")
async def logout(request: Request, response: Response):
    req_id = getattr(request.state, "req_id", "N/A")
    ip = getattr(request.state, "client_ip", "unknown")
    
    user = getattr(request.state, "user", None)
    who = user.get("sub") if user else "Unknown"
    
    clear_auth_cookies(response)
    log_event(who=who, what="LOGOUT", where="/logout", details="", ip=ip, req_id=req_id)
    return {"status": "success"}
