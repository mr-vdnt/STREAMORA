from __future__ import annotations
import logging
from datetime import datetime
from typing import Optional
from services.repository.catalog_db import CatalogRepository, SearchSession, SearchEvent

logger = logging.getLogger("streamora.search.telemetry")

class SearchTelemetryLogger:
    """
    SearchSession & SearchEvent Telemetry Logger.
    Logs telemetry across query executions, result clicks, dwell times, and query reformulations.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    def log_query_event(
        self, 
        query_text: str, 
        rewritten_query: str, 
        intent: str, 
        plan_hash: str, 
        results_count: int, 
        latency_ms: float, 
        session_id: Optional[int] = None
    ) -> int:
        session = self.repo.get_session()
        try:
            evt = SearchEvent(
                session_id=session_id,
                query_text=query_text,
                rewritten_query=rewritten_query,
                parsed_intent=intent,
                plan_hash=plan_hash,
                results_count=results_count,
                latency_ms=round(latency_ms, 2),
                event_type="query"
            )
            session.add(evt)
            session.commit()
            return evt.id
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to log search telemetry query event: {e}")
            return 0
        finally:
            session.close()

    def log_click_event(self, event_id: int, clicked_content_id: int, position: int, dwell_seconds: Optional[float] = None) -> None:
        session = self.repo.get_session()
        try:
            evt = session.query(SearchEvent).filter(SearchEvent.id == event_id).first()
            if evt:
                evt.clicked_content_id = clicked_content_id
                evt.click_position = position
                evt.dwell_time_seconds = dwell_seconds
                evt.event_type = "click"
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to log search telemetry click event: {e}")
        finally:
            session.close()
