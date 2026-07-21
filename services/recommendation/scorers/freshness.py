from typing import Dict, Any
from services.recommendation.scorers.base_scorer import BaseScorer

class FreshnessScorer(BaseScorer):
    @property
    def default_weight(self) -> float:
        return 0.10

    def score(self, movie: Dict[str, Any], context: Dict[str, Any] = None) -> float:
        return self._calculate_freshness(str(movie.get('year', '')))

    def _calculate_freshness(self, year_str: str) -> float:
        import datetime
        try:
            year = int(year_str)
            current_year = datetime.datetime.now().year
            age = current_year - year
            if age <= 0: return 1.0
            if age <= 2: return 0.8
            if age <= 5: return 0.5
            if age <= 10: return 0.3
            return 0.1
        except:
            return 0.1
