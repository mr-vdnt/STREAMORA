"""
Interaction Label Generator & Event Weight Differential for Streamora Phase 6.1.

Converts multi-event telemetry hierarchies into defensible, weighted training labels (y).
Prevents impression bias by assigning higher weight to completed watches and explicit likes.
"""
from dataclasses import dataclass
from typing import Dict, List, Any


class LabelGenerator:
    """Computes weighted ordinal ranking labels for LTR training datasets."""

    EVENT_WEIGHTS = {
        "impression": 0.05,
        "click": 0.20,
        "detail_view": 0.30,
        "playback_start": 0.50,
        "watchlist": 0.90,
        "completion": 1.00,
        "like": 1.00,
        "dislike": -1.50
    }

    @classmethod
    def compute_label(cls, events: List[Dict[str, Any]]) -> float:
        """Computes label y for a specific user-content interaction sequence."""
        if not events:
            return 0.0

        total_score = 0.0
        has_dislike = False

        for ev in events:
            ev_type = ev.get("event_type", "impression").lower()
            weight = cls.EVENT_WEIGHTS.get(ev_type, 0.05)
            if ev_type == "dislike":
                has_dislike = True
            total_score += weight

        if has_dislike:
            return max(0.0, total_score)
        return min(1.0, max(0.0, total_score))
