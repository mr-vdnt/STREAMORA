from typing import Dict, Any
from services.recommendation.scorers.base_scorer import BaseScorer

class QualityScorer(BaseScorer):
    @property
    def default_weight(self) -> float:
        return 0.15

    def score(self, movie: Dict[str, Any], context: Dict[str, Any] = None) -> float:
        context = context or {}
        return float(movie.get('rating', 0) or 0) / 10.0
