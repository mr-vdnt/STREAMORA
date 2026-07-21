from typing import Dict, Any
from services.recommendation.scorers.base_scorer import BaseScorer

class FranchiseScorer(BaseScorer):
    @property
    def default_weight(self) -> float:
        return 0.10

    def score(self, movie: Dict[str, Any], context: Dict[str, Any] = None) -> float:
        context = context or {}
        # Simple franchise matching dummy logic for now
        return float(context.get('same_franchise', 0.0))
