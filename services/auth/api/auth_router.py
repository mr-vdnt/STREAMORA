from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from services.repository.catalog_db import CatalogRepository, UserAccount, HouseholdProfile
from services.auth.jwt_auth import hash_password, verify_password, create_access_token, get_current_user_account

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
repo = CatalogRepository()

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

@auth_router.post("/register")
def register_user(req: RegisterRequest):
    with repo.get_session() as session:
        existing = session.query(UserAccount).filter(UserAccount.email == req.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        user = UserAccount(
            email=req.email,
            hashed_password=hash_password(req.password),
            full_name=req.full_name or req.email.split("@")[0]
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Create default primary household profile
        profile = HouseholdProfile(
            account_id=user.id,
            profile_name="Main",
            is_kids=False
        )
        session.add(profile)
        session.commit()

        token = create_access_token({"sub": user.email, "user_id": user.id})
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {"id": user.id, "email": user.email, "full_name": user.full_name}
        }

@auth_router.post("/login")
def login_user(req: LoginRequest):
    with repo.get_session() as session:
        user = session.query(UserAccount).filter(UserAccount.email == req.email).first()
        if not user or not verify_password(req.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = create_access_token({"sub": user.email, "user_id": user.id})
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {"id": user.id, "email": user.email, "full_name": user.full_name}
        }

@auth_router.get("/me")
def get_me(user: dict = Depends(get_current_user_account)):
    return user
