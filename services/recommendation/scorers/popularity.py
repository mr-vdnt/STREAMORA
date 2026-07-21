from typing import Dict, Any
from services.recommendation.scorers.base_scorer import BaseScorer

class PopularityScorer(BaseScorer):
    @property
    def default_weight(self) -> float:
        return 0.20

    def score(self, movie: Dict[str, Any], context: Dict[str, Any] = None) -> float:
        context = context or {}
        return min(float(movie.get('popularity', 0) or 0) / 100.0, 1.0)
