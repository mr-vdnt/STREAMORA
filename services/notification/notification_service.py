from __future__ import annotations
from typing import Dict, List, Optional, Any
from services.repository.catalog_db import CatalogRepository, UserNotification

class NotificationService:
    """Notification platform for continue watching alerts, new releases, and system messages."""

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    def send_notification(
        self,
        account_id: int,
        title: str,
        message: str,
        notification_type: str = "info",
        link_url: Optional[str] = None
    ) -> Dict[str, Any]:
        with self.repo.get_session() as session:
            notif = UserNotification(
                account_id=account_id,
                title=title,
                message=message,
                notification_type=notification_type,
                link_url=link_url
            )
            session.add(notif)
            session.commit()
            session.refresh(notif)

            return {
                "id": notif.id,
                "account_id": notif.account_id,
                "title": notif.title,
                "message": notif.message,
                "notification_type": notif.notification_type,
                "is_read": notif.is_read
            }

    def get_user_notifications(self, account_id: int, unread_only: bool = False) -> List[Dict[str, Any]]:
        with self.repo.get_session() as session:
            query = session.query(UserNotification).filter(UserNotification.account_id == account_id)
            if unread_only:
                query = query.filter(UserNotification.is_read == False)

            notifs = query.order_by(UserNotification.created_at.desc()).all()
            return [
                {
                    "id": n.id,
                    "title": n.title,
                    "message": n.message,
                    "notification_type": n.notification_type,
                    "link_url": n.link_url,
                    "is_read": n.is_read,
                    "created_at": n.created_at.isoformat()
                }
                for n in notifs
            ]

    def mark_as_read(self, notification_id: int) -> bool:
        with self.repo.get_session() as session:
            notif = session.query(UserNotification).filter(UserNotification.id == notification_id).first()
            if notif:
                notif.is_read = True
                session.commit()
                return True
            return False
