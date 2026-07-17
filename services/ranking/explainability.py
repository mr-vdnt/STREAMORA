from .models import FeatureVector, Explainability

class ExplainabilityEngine:
    """Generates structured reasoning for a candidate."""
    
    def explain(self, fv: FeatureVector) -> Explainability:
        reason_codes = []
        reason_scores = {}
        
        if fv.director_match:
            code = "DIRECTOR_MATCH"
            reason_codes.append(code)
            reason_scores[code] = 1.0
            
        if fv.franchise_match:
            code = "FRANCHISE_MATCH"
            reason_codes.append(code)
            reason_scores[code] = 1.0
            
        if fv.genre_overlap_pct >= 0.5:
            code = "GENRE_MATCH"
            reason_codes.append(code)
            reason_scores[code] = fv.genre_overlap_pct
            
        if fv.theme_overlap_pct > 0:
            code = "THEME_MATCH"
            reason_codes.append(code)
            reason_scores[code] = fv.theme_overlap_pct
            
        if fv.actor_match_count > 0:
            code = "ACTOR_MATCH"
            reason_codes.append(code)
            reason_scores[code] = min(fv.actor_match_count / 3.0, 1.0)
            
        if fv.retrieval_fusion_score > 0.05:
            code = "HIGH_SEMANTIC_SIMILARITY"
            reason_codes.append(code)
            reason_scores[code] = fv.retrieval_fusion_score
            
        return Explainability(reason_codes=reason_codes, reason_scores=reason_scores)
