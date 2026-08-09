from __future__ import annotations
import math
import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

logger = logging.getLogger("streamora.events.telemetry")

EVENT_WEIGHT_MAP = {
    "impression": 0.05,
    "click": 0.20,
    "detail_view": 0.30,
    "trailer_start": 0.40,
    "trailer_complete": 0.70,
    "playback_start": 0.50,
    "progress": 0.60,
    "completion": 1.00,
    "watchlist_add": 0.80,
    "like": 1.20,
    "dislike": -1.00,
    "search_select": 0.40
}

@dataclass
class TelemetryEventDTO:
    event_id: str
    user_id: str
    event_type: str
    content_id: Optional[int] = None
    categories: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

class PreferenceLearningEngine:
    """
    Event-driven Telemetry Ingestion & Temporal Decay Preference Learning Engine.
    Idempotently processes user interaction events and updates genre/category preference weights.
    """

    def __init__(self):
        self._user_weights: Dict[str, Dict[str, float]] = {}
        self._processed_events: set[str] = set()

    def process_event_batch(self, events: List[TelemetryEventDTO]) -> Dict[str, Any]:
        processed_count = 0
        skipped_count = 0

        for event in events:
            if event.event_id in self._processed_events:
                skipped_count += 1
                continue

            self._processed_events.add(event.event_id)
            processed_count += 1

            weight_delta = EVENT_WEIGHT_MAP.get(event.event_type, 0.10)
            user_id = event.user_id

            if user_id not in self._user_weights:
                self._user_weights[user_id] = {}

            for cat in event.categories:
                current_weight = self._user_weights[user_id].get(cat, 0.0)
                # Apply exponential decay to previous weight
                decayed_weight = current_weight * 0.98
                self._user_weights[user_id][cat] = round(decayed_weight + weight_delta, 4)

        return {
            "processed_count": processed_count,
            "skipped_count": skipped_count,
            "status": "SUCCESS"
        }

    def get_user_preference_profile(self, user_id: str) -> Dict[str, float]:
        return self._user_weights.get(user_id, {})
