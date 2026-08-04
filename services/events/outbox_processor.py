from __future__ import annotations
from typing import Dict, List, Any
from services.repository.catalog_db import CatalogRepository, OutboxEvent
from services.events.event_bus import EventBus

class OutboxProcessor:
    """Transactional Outbox Pattern processor guaranteeing at-least-once event delivery."""

    def __init__(self, repo: CatalogRepository = None, event_bus: EventBus = None):
        self.repo = repo or CatalogRepository()
        self.event_bus = event_bus or EventBus()

    def process_pending_outbox_events(self, limit: int = 100) -> int:
        with self.repo.get_session() as session:
            events = session.query(OutboxEvent).filter(
                OutboxEvent.processed == False
            ).limit(limit).all()

            processed_count = 0
            for event in events:
                import json
                payload = json.loads(event.payload_json) if event.payload_json else {}
                self.event_bus.publish(event.event_type, payload)
                event.processed = True
                processed_count += 1

            session.commit()
            return processed_count
