from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Optional, Any
from services.repository.catalog_db import CatalogRepository, WatchHistory

class WatchHistoryService:
    """
    Immutable Watch History Engine.
    Records permanent viewing history timeline logs, separate from mutable WatchProgress heartbeats.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    def record_watch_event(
        self,
        account_id: int,
        content_id: int,
        duration_watched_seconds: float,
        completed: bool = False,
        profile_id: Optional[int] = None
    ) -> Dict[str, Any]:
        with self.repo.get_session() as session:
            entry = WatchHistory(
                account_id=account_id,
                profile_id=profile_id,
                content_id=content_id,
                duration_watched_seconds=duration_watched_seconds,
                completed=completed,
                watched_at=datetime.utcnow()
            )
            session.add(entry)
            session.commit()
            session.refresh(entry)

            return {
                "id": entry.id,
                "account_id": entry.account_id,
                "content_id": entry.content_id,
                "duration_watched_seconds": entry.duration_watched_seconds,
                "completed": entry.completed,
                "watched_at": entry.watched_at.isoformat()
            }

    def get_user_history(self, account_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        with self.repo.get_session() as session:
            records = session.query(WatchHistory).filter(
                WatchHistory.account_id == account_id
            ).order_by(WatchHistory.watched_at.desc()).limit(limit).all()

            results = []
            for r in records:
                content = self.repo.get_by_id(r.content_id)
                results.append({
                    "id": r.id,
                    "content_id": r.content_id,
                    "content": content,
                    "duration_watched_seconds": r.duration_watched_seconds,
                    "completed": r.completed,
                    "watched_at": r.watched_at.isoformat()
                })
            return results
