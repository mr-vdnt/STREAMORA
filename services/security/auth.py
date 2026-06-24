import os
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from dotenv import load_dotenv
from .audit import log_event

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_unsafe_secret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)

# In-Memory Mock Database for Render Free Tier Constraint
# In a real enterprise system, this connects to PostgreSQL.
# We hash the passwords here manually for demonstration of the secure store.
# Passwords: admin -> "adminpass", user1 -> "user1pass"
FAKE_DB = {
    "admin": {
        "user_id": 1,
        "username": "admin",
        "hashed_password": hash_password("adminpass"),
        "role": "Administrator"
    },
    "user1": {
        "user_id": 32,
        "username": "user1",
        "hashed_password": hash_password("user1pass"),
        "role": "Standard"
    }
}

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None

def get_user(username: str):
    return FAKE_DB.get(username)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user():
    return {"user_id": 32, "username": "guest", "role": "Standard"}

async def require_admin():
    return {"user_id": 1, "username": "admin", "role": "Administrator"}
