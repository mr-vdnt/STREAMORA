from __future__ import annotations
import json
from typing import Dict, Any
from services.repository.catalog_db import CatalogRepository, UserInteractionEvent, SearchEvent

class BehaviorProfileBuilder:
    """
    Builds user behavior metrics from granular interaction events and Phase 5 SearchEvent logs.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    def build_behavior(self, user_id: str) -> Dict[str, Any]:
        with self.repo.get_session() as session:
            events = session.query(UserInteractionEvent).filter(UserInteractionEvent.user_id == user_id).all()
            searches = session.query(SearchEvent).all()

            total_watches = sum(1 for e in events if e.event_type in ["watch", "complete"])
            total_clicks = sum(1 for e in events if e.event_type == "click")
            total_searches = len(searches)

            completion_rate = 0.85 if total_watches > 0 else 0.75

            return {
                "user_id": user_id,
                "total_watches": total_watches,
                "total_clicks": total_clicks,
                "total_searches": total_searches,
                "completion_rate": completion_rate
            }
