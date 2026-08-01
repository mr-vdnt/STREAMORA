from __future__ import annotations
from datetime import datetime
from typing import Dict, Any

class ContextProfileBuilder:
    """
    Builds temporal, device, and environmental context profiles.
    """

    def build_context(self, device: str = "web", language: str = "en") -> Dict[str, Any]:
        now = datetime.utcnow()
        is_weekend = now.weekday() >= 5
        hour = now.hour

        if 6 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 18:
            time_of_day = "afternoon"
        elif 18 <= hour < 23:
            time_of_day = "evening"
        else:
            time_of_day = "late_night"

        return {
            "device": device,
            "language": language,
            "is_weekend": is_weekend,
            "time_of_day": time_of_day,
            "hour": hour
        }
