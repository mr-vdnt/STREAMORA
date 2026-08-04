from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Optional, Any
from services.repository.catalog_db import CatalogRepository, WatchProgress, UserInteractionEvent
from services.recommendation.analytics.telemetry import FeedbackTelemetryLogger

class PlaybackService:
    """
    Workstream 4 Playback Service.
    Handles video stream URL resolution, real-time heartbeat progress sync, and watch resume capabilities.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()
        self.telemetry = FeedbackTelemetryLogger(self.repo)

    def get_stream_manifest(self, content_id: int, quality: str = "1080p") -> Dict[str, Any]:
        content = self.repo.get_by_id(content_id)
        title = content.get("title", f"Content #{content_id}") if content else f"Content #{content_id}"

        return {
            "content_id": content_id,
            "title": title,
            "stream_format": "HLS",
            "quality": quality,
            "stream_url": f"https://demo.streamora.ai/streams/{content_id}/master.m3u8",
            "subtitles": [
                {"language": "English", "code": "en", "url": f"https://demo.streamora.ai/subs/{content_id}_en.vtt"},
                {"language": "Spanish", "code": "es", "url": f"https://demo.streamora.ai/subs/{content_id}_es.vtt"}
            ],
            "audio_tracks": [
                {"language": "English Dolby Atmos", "code": "en-atmos"}
            ]
        }

    def sync_watch_progress(
        self,
        account_id: int,
        content_id: int,
        progress_seconds: float,
        duration_seconds: float,
        profile_id: Optional[int] = None
    ) -> Dict[str, Any]:
        is_completed = (progress_seconds / duration_seconds) >= 0.90 if duration_seconds > 0 else False

        with self.repo.get_session() as session:
            record = session.query(WatchProgress).filter(
                WatchProgress.account_id == account_id,
                WatchProgress.content_id == content_id
            ).first()

            if not record:
                record = WatchProgress(
                    account_id=account_id,
                    profile_id=profile_id,
                    content_id=content_id,
                    progress_seconds=progress_seconds,
                    duration_seconds=duration_seconds,
                    is_completed=is_completed
                )
                session.add(record)
            else:
                record.progress_seconds = progress_seconds
                record.duration_seconds = duration_seconds
                record.is_completed = is_completed
                record.last_watched_at = datetime.utcnow()
            
            session.commit()

        # Feed real-time implicit telemetry into Recommendation Intelligence Platform (RIP)
        self.telemetry.log_interaction(
            user_id=str(account_id),
            content_id=content_id,
            event_type="watch_progress",
            weight=1.0 if not is_completed else 2.5,
            context={"progress_seconds": progress_seconds, "is_completed": is_completed}
        )

        return {
            "account_id": account_id,
            "content_id": content_id,
            "progress_seconds": progress_seconds,
            "duration_seconds": duration_seconds,
            "is_completed": is_completed,
            "synced_at": datetime.utcnow().isoformat()
        }

    def get_continue_watching(self, account_id: int) -> List[Dict[str, Any]]:
        with self.repo.get_session() as session:
            records = session.query(WatchProgress).filter(
                WatchProgress.account_id == account_id,
                WatchProgress.is_completed == False
            ).order_by(WatchProgress.last_watched_at.desc()).limit(10).all()

            results = []
            for r in records:
                content = self.repo.get_by_id(r.content_id)
                if content:
                    item = dict(content)
                    item["watch_progress"] = {
                        "progress_seconds": r.progress_seconds,
                        "duration_seconds": r.duration_seconds,
                        "percent_complete": round((r.progress_seconds / r.duration_seconds) * 100, 1) if r.duration_seconds > 0 else 0
                    }
                    results.append(item)
            return results
