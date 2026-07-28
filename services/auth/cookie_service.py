import os
import secrets
from fastapi import Response
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

# HttpOnly cookie config
SECURE_COOKIES = os.getenv("ENVIRONMENT", "development").lower() == "production"

def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    """Sets HttpOnly cookies for access and refresh tokens, and a CSRF token."""
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=SECURE_COOKIES,
        samesite="lax",
        max_age=15 * 60, # 15 minutes
        path="/"
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=SECURE_COOKIES,
        samesite="lax",
        max_age=30 * 24 * 60 * 60, # 30 days
        path="/auth/refresh" # Restrict refresh token to refresh endpoint
    )
    
    # Generate and set CSRF Token (Accessible to JavaScript)
    csrf_token = secrets.token_hex(32)
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=SECURE_COOKIES,
        samesite="lax",
        max_age=30 * 24 * 60 * 60,
        path="/"
    )
    return csrf_token

def clear_auth_cookies(response: Response):
    """Clears authentication cookies."""
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/auth/refresh")
    response.delete_cookie("csrf_token", path="/")
