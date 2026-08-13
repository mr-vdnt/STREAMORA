"""
Real-Time Preference Learner & Temporal Preference Vector Update Engine.

Applies interaction event weights and exponential temporal decay:
  weight(t) = weight_0 * e^(-lambda * delta_t)

Enforces event hierarchy:
  impression (0.05) << click (0.20) << watchlist (0.90) << completion (1.0) << like (1.0) / dislike (-1.5)
"""
import math
from datetime import datetime, timezone
from typing import Dict, List, Any


class PreferenceLearner:
    """Updates user preference vectors with event-weighted signals and temporal decay."""

    EVENT_WEIGHTS = {
        "impression": 0.05,
        "click": 0.20,
        "detail_view": 0.30,
        "trailer_start": 0.40,
        "playback_start": 0.60,
        "progress_50": 0.80,
        "completion": 1.00,
        "watchlist_add": 0.90,
        "like": 1.00,
        "dislike": -1.50
    }

    HALF_LIFE_DAYS = 30.0
    LAMBDA = math.log(2) / HALF_LIFE_DAYS  # Decay factor

    def calculate_event_signal(self, event_type: str, timestamp: datetime, now: datetime | None = None) -> float:
        """Calculate event strength with exponential temporal decay."""
        base_weight = self.EVENT_WEIGHTS.get(event_type.lower(), 0.10)
        if now is None:
            now = datetime.now(timezone.utc)

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        delta_seconds = max(0.0, (now - timestamp).total_seconds())
        delta_days = delta_seconds / 86400.0
        decay_factor = math.exp(-self.LAMBDA * delta_days)
        return round(base_weight * decay_factor, 6)

    def update_user_vector(
        self,
        current_vector: Dict[str, float],
        interaction_events: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Update preference vector across genres/themes with new interactions."""
        updated_vector = current_vector.copy()

        for event in interaction_events:
            event_type = event.get("event_type", "impression")
            ts = event.get("timestamp", datetime.now(timezone.utc))
            genres = event.get("genres", [])
            signal = self.calculate_event_signal(event_type, ts)

            for genre in genres:
                key = genre.lower()
                current_score = updated_vector.get(key, 0.50)
                # Exponential moving average / smooth update
                updated_vector[key] = max(0.0, min(1.0, current_score + signal * 0.10))

        return updated_vector
