from __future__ import annotations
import math
from datetime import datetime, timedelta

class FreshnessScorer:
    """
    Exponential Time Decay & Freshness Scoring Engine.
    Applies time decay formula S_final = S_base * e^(-lambda * days) to prevent legacy items from dominating.
    """

    def __init__(self, decay_rate_lambda: float = 0.005):
        self.decay_rate_lambda = decay_rate_lambda

    def calculate_decay_score(self, base_score: float, release_date_str: str) -> float:
        try:
            rel_date = datetime.strptime(release_date_str, "%Y-%m-%d")
        except Exception:
            rel_date = datetime.utcnow() - timedelta(days=365)

        age_days = (datetime.utcnow() - rel_date).days
        age_days = max(0, age_days)

        decay_factor = math.exp(-self.decay_rate_lambda * age_days)
        return base_score * decay_factor
