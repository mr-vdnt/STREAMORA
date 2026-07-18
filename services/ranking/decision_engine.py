import time
from typing import List, Dict, Any

from .models import RecommendationPackage, Recommendation, RankingMetadata, DecisionDiagnostics
from .business_rules import BusinessRuleEngine
from .features import FeatureExtractor
from .scoring import ScoringEngine
from .confidence import ConfidenceEstimator
from .explainability import ExplainabilityEngine
from .diversity import DiversityOptimizer

class DecisionEngine:
    def __init__(self, movies_db: dict, user_adapter=None, content_adapter=None):
        self.movies_db = movies_db
        self.rule_engine = BusinessRuleEngine(movies_db)
        self.extractor = FeatureExtractor(movies_db, user_adapter, content_adapter)
        self.scorer = ScoringEngine()
        self.confidence_estimator = ConfidenceEstimator()
        self.explainability_engine = ExplainabilityEngine()
        self.diversity_optimizer = DiversityOptimizer()
        
    def _timer(self) -> float:
        return time.perf_counter()
        
    def process(self, candidate_pool: dict) -> RecommendationPackage:
        t_start = self._timer()
        diagnostics = DecisionDiagnostics()
        
        query_contract = candidate_pool.get("query_contract", {})
        candidates = candidate_pool.get("candidates", [])
        diagnostics.candidates_in = len(candidates)
        
        # 1. Business Rules (Deduplication, Reference removal)
        t_rules_start = self._timer()
        valid_candidates = self.rule_engine.filter(candidates, query_contract)
        diagnostics.duplicates_removed = diagnostics.candidates_in - len(valid_candidates)
        diagnostics.business_rules_ms = int((self._timer() - t_rules_start) * 1000)
        
        # 2. Feature Extraction, Scoring, Confidence, Explainability
        t_extract_start = self._timer()
        recommendations = []
        
        for c in valid_candidates:
            # Extract
            fv = self.extractor.extract(c, query_contract)
            
            # Score
            score = self.scorer.score(fv)
            
            # Confidence
            conf = self.confidence_estimator.estimate(c, fv)
            
            # Explainability
            explain = self.explainability_engine.explain(fv)
            
            rank_meta = RankingMetadata(rank=0, recommendation_score=score, confidence=conf)
            
            rec = Recommendation(
                content_id=c["content_id"],
                ranking=rank_meta,
                explainability=explain,
                features=fv
            )
            recommendations.append(rec)
            
        diagnostics.feature_extraction_ms = int((self._timer() - t_extract_start) * 1000)
        # Note: scoring, confidence, and explainability happen per candidate, grouped in extraction time for simplicity, 
        # or we could measure scoring specifically. For now, tracking combined as feature_extraction_ms.
        
        # 3. Sort by Score (Initial Ranking)
        t_sort_start = self._timer()
        recommendations.sort(key=lambda r: r.ranking.recommendation_score, reverse=True)
        diagnostics.scoring_ms = int((self._timer() - t_sort_start) * 1000)
        
        # 4. Diversity Optimization
        t_div_start = self._timer()
        diversified_recs = self.diversity_optimizer.optimize(recommendations, self.movies_db)
        diagnostics.diversity_replacements = len(recommendations) - len(diversified_recs)
        diagnostics.diversity_ms = int((self._timer() - t_div_start) * 1000)
        
        # 5. Packaging (Assign Final Ranks & Build Package)
        t_pack_start = self._timer()
        
        final_recs = []
        # Limit to top 10 for final recommendations
        top_k = diversified_recs[:10]
        
        for idx, rec in enumerate(top_k):
            rec.ranking.rank = idx + 1
            final_recs.append(rec)
            
        diagnostics.recommendations_out = len(final_recs)
        diagnostics.packaging_ms = int((self._timer() - t_pack_start) * 1000)
        
        diagnostics.total_ms = int((self._timer() - t_start) * 1000)
        
        return RecommendationPackage(
            recommendations=final_recs,
            diagnostics=diagnostics
        )
