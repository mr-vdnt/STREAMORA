from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from services.admin.admin_service import AdminPlatformService
from services.auth.jwt_auth import get_current_user_account

admin_router = APIRouter(prefix="/admin", tags=["Admin CMS & Operations"])
service = AdminPlatformService()

class CollectionOverrideRequest(BaseModel):
    slug: str
    title: str
    description: str
    content_ids: List[int]
    category: Optional[str] = "spotlight"

def require_admin(user: dict = Depends(get_current_user_account)):
    if not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user

@admin_router.get("/overview")
def get_overview(admin: dict = Depends(require_admin)):
    return service.get_system_overview()

@admin_router.get("/users")
def list_users(admin: dict = Depends(require_admin)):
    return {"users": service.list_users()}

@admin_router.post("/collections/override")
def create_collection_override(
    req: CollectionOverrideRequest,
    admin: dict = Depends(require_admin)
):
    return service.create_collection_override(
        slug=req.slug,
        title=req.title,
        description=req.description,
        content_ids=req.content_ids,
        category=req.category
    )
