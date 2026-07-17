from .models import FeatureVector
from .config.weights import WEIGHTS

class ScoringEngine:
    """Calculates final recommendation score based on configured weights."""
    
    def __init__(self, weights: dict = None):
        self.weights = weights or WEIGHTS
        
    def score(self, fv: FeatureVector) -> float:
        final_score = 0.0
        
        # Base Retrieval
        final_score += fv.retrieval_fusion_score * self.weights.get("retrieval_fusion_score", 0.0)
        
        # Overlaps
        final_score += fv.genre_overlap_pct * self.weights.get("genre_overlap", 0.0)
        final_score += fv.theme_overlap_pct * self.weights.get("theme_overlap", 0.0)
        
        if fv.director_match:
            final_score += self.weights.get("director_match", 0.0)
            
        if fv.actor_match_count > 0:
            # Diminishing returns for multiple actors, but simple heuristic for now
            final_score += self.weights.get("actor_match", 0.0) * min(fv.actor_match_count, 3)
            
        # Popularity (Normalize 0-100 to 0-1 roughly)
        pop_norm = min(fv.popularity / 100.0, 1.0)
        final_score += pop_norm * self.weights.get("popularity_boost", 0.0)
        
        # Vote Average (Normalize 0-10 to 0-1)
        vote_norm = fv.vote_average / 10.0
        final_score += vote_norm * self.weights.get("vote_average_boost", 0.0)
        
        return final_score
