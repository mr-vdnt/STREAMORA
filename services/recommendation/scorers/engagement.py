from typing import Dict, Any
from services.recommendation.scorers.base_scorer import BaseScorer

class EngagementScorer(BaseScorer):
    @property
    def default_weight(self) -> float:
        return 0.05

    def score(self, movie: Dict[str, Any], context: Dict[str, Any] = None) -> float:
        context = context or {}
        return float(context.get('engagement', 0.0))
