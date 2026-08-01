from __future__ import annotations
import logging
from typing import Optional, Dict, Any
from services.repository.catalog_db import CatalogRepository, UserInteractionEvent, RecommendationEvent, RecommendationFeedback

logger = logging.getLogger("streamora.recommendation.telemetry")

class FeedbackTelemetryLogger:
    """
    Layer 10 Implicit & Explicit Feedback Telemetry Logger.
    Logs telemetry across slate rendering, item clicks, dwell times, and explicit ratings.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    def log_interaction(
        self, 
        user_id: str, 
        content_id: int, 
        event_type: str, 
        weight: float = 1.0, 
        context: Optional[Dict[str, Any]] = None
    ) -> int:
        session = self.repo.get_session()
        try:
            evt = UserInteractionEvent(
                user_id=user_id,
                content_id=content_id,
                event_type=event_type,
                weight=weight,
                context_metadata_json=str(context) if context else None
            )
            session.add(evt)

            # Mirror to Feedback table if explicit
            if event_type in ["like", "dislike", "rate", "watchlist"]:
                fb = RecommendationFeedback(
                    user_id=user_id,
                    content_id=content_id,
                    feedback_type=event_type,
                    score=weight
                )
                session.add(fb)

            session.commit()
            return evt.id
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to log recommendation telemetry interaction: {e}")
            return 0
        finally:
            session.close()
