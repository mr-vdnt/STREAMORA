from __future__ import annotations
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from services.events.telemetry_processor import PreferenceLearningEngine, TelemetryEventDTO

logger = logging.getLogger("streamora.events.outbox")

@dataclass
class OutboxEventRecord:
    event_id: str
    user_id: str
    event_type: str
    payload: Dict[str, Any]
    status: str = "PENDING"  # PENDING, PROCESSED, FAILED
    created_at: float = field(default_factory=time.time)

class OutboxEventProcessor:
    """
    Durable Outbox Event Processor.
    Consumes pending events from outbox log and dispatches them asynchronously to preference & feature workers.
    """

    def __init__(self, learning_engine: Optional[PreferenceLearningEngine] = None):
        self._outbox_queue: List[OutboxEventRecord] = []
        self.learning_engine = learning_engine or PreferenceLearningEngine()

    def enqueue_event(self, record: OutboxEventRecord):
        self._outbox_queue.append(record)

    def process_pending_outbox(self) -> Dict[str, Any]:
        pending = [e for e in self._outbox_queue if e.status == "PENDING"]
        if not pending:
            return {"processed_count": 0, "status": "NO_PENDING_EVENTS"}

        dtos = []
        for record in pending:
            dtos.append(TelemetryEventDTO(
                event_id=record.event_id,
                user_id=record.user_id,
                event_type=record.event_type,
                categories=record.payload.get("categories", []),
                content_id=record.payload.get("content_id")
            ))
            record.status = "PROCESSED"

        res = self.learning_engine.process_event_batch(dtos)
        return {
            "processed_count": len(pending),
            "learning_engine_result": res,
            "status": "SUCCESS"
        }
