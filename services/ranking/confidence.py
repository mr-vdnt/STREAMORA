from .models import FeatureVector

class ConfidenceEstimator:
    """Estimates confidence independently of the recommendation score."""
    
    def estimate(self, candidate_dict: dict, fv: FeatureVector) -> float:
        # Base confidence from generators
        generators = candidate_dict.get("retrieval", {}).get("generators", [])
        num_generators = len(generators)
        
        confidence = 0.5 # Baseline
        
        # Agreement across multiple generators raises confidence significantly
        if num_generators >= 3:
            confidence += 0.3
        elif num_generators == 2:
            confidence += 0.15
            
        # Missing critical metadata lowers confidence
        if fv.vote_count < 10 or fv.popularity < 1.0:
            confidence -= 0.1
            
        # Exact overlaps increase confidence
        if fv.director_match or fv.franchise_match:
            confidence += 0.1
            
        return max(0.0, min(1.0, confidence))
