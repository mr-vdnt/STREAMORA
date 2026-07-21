from typing import Dict, Any

class BaseScorer:
    """
    Abstract base class for all Recommendation Engine scorers.
    """
    @property
    def name(self) -> str:
        """Name of the scorer for debugging and logging."""
        return self.__class__.__name__

    @property
    def default_weight(self) -> float:
        """Default weight if not overridden in the configuration."""
        return 1.0

    def score(self, movie: Dict[str, Any], context: Dict[str, Any] = None) -> float:
        """
        Calculates the score for a single movie.
        Should return a normalized float between 0.0 and 1.0.
        """
        raise NotImplementedError("Scorer must implement the score() method.")
