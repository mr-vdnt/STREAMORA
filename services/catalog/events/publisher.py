import json
from datetime import datetime
from sqlalchemy.orm import Session
from services.repository.catalog_db import OutboxEvent

class OutboxEventPublisher:
    """
    Transactional Outbox Pattern Publisher.
    Ensures domain events are persisted inside DB transaction before dispatching.
    """
    @staticmethod
    def publish(session: Session, aggregate_type: str, aggregate_id: str, event_type: str, payload: dict) -> OutboxEvent:
        event = OutboxEvent(
            aggregate_type=aggregate_type,
            aggregate_id=str(aggregate_id),
            event_type=event_type,
            payload=json.dumps(payload),
            processed=False,
            created_at=datetime.utcnow()
        )
        session.add(event)
        return event
