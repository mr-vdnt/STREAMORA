import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from dotenv import load_dotenv
from .audit import log_event

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_unsafe_secret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)

# In-Memory Mock Database for Render Free Tier Constraint
# In a real enterprise system, this connects to PostgreSQL.
# We hash the passwords here manually for demonstration of the secure store.
# Passwords: admin -> "adminpass", user1 -> "user1pass"
FAKE_DB = {
    "admin": {
        "user_id": 1,
        "username": "admin",
        "hashed_password": pwd_context.hash("adminpass"),
        "role": "Administrator"
    },
    "user1": {
        "user_id": 32,
        "username": "user1",
        "hashed_password": pwd_context.hash("user1pass"),
        "role": "Standard"
    }
}

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

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

async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)):
    if not token:
        # Default guest access (using user1's profile context)
        return {"user_id": 32, "username": "guest", "role": "Standard"}
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        user_id: int = payload.get("user_id")
        if username is None or role is None:
            return {"user_id": 32, "username": "guest", "role": "Standard"}
        token_data = TokenData(username=username, role=role, user_id=user_id)
    except JWTError:
        return {"user_id": 32, "username": "guest", "role": "Standard"}
    
    user = get_user(username=token_data.username)
    if user is None:
        return {"user_id": 32, "username": "guest", "role": "Standard"}
    return user

async def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "Administrator":
        log_event(
            who=current_user.get("username"),
            what="UNAUTHORIZED_ADMIN_ACCESS",
            where="require_admin",
            details="Attempted to access protected admin endpoint."
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have enough privileges."
        )
    return current_user
