from typing import Dict, Any
from services.recommendation.scorers.base_scorer import BaseScorer

class RegionalScorer(BaseScorer):
    @property
    def default_weight(self) -> float:
        return 0.25

    def score(self, movie: Dict[str, Any], context: Dict[str, Any] = None) -> float:
        context = context or {}
        return 1.0 if str(movie.get('language', '')).lower() in ['hi', 'ta', 'te', 'ml', 'kn', 'bn', 'mr', 'pa', 'gu'] or 'bollywood' in str(movie.get('genres', '')).lower() else 0.0
