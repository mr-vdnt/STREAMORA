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
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

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

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        user_id: int = payload.get("user_id")
        if username is None or role is None:
            raise credentials_exception
        token_data = TokenData(username=username, role=role, user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

import json

USERS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/users.json"))

def load_users_db():
    global FAKE_DB
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                data = json.load(f)
                for k, v in data.items():
                    FAKE_DB[k] = v
        except Exception as e:
            print("Error loading users database:", e)

def save_users_db():
    try:
        os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
        with open(USERS_FILE, "w") as f:
            json.dump(FAKE_DB, f, indent=4)
    except Exception as e:
        print("Error saving users database:", e)

# Load database on startup
load_users_db()

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
