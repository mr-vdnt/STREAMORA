from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from services.notification.notification_service import NotificationService
from services.auth.jwt_auth import get_current_user_account

notification_router = APIRouter(prefix="/notifications", tags=["Notification Engine"])
service = NotificationService()

class SendNotificationRequest(BaseModel):
    account_id: int
    title: str
    message: str
    notification_type: Optional[str] = "info"
    link_url: Optional[str] = None

@notification_router.get("/")
def get_notifications(
    unread_only: bool = Query(False),
    user: dict = Depends(get_current_user_account)
):
    account_id = user.get("id", 1)
    notifs = service.get_user_notifications(account_id, unread_only)
    return {"notifications": notifs, "count": len(notifs)}

@notification_router.post("/send")
def send_notification(req: SendNotificationRequest):
    return service.send_notification(
        account_id=req.account_id,
        title=req.title,
        message=req.message,
        notification_type=req.notification_type,
        link_url=req.link_url
    )

@notification_router.post("/read/{notification_id}")
def mark_read(notification_id: int):
    success = service.mark_as_read(notification_id)
    return {"success": success}
