from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import time

class FeatureVector(BaseModel):
    retrieval_fusion_score: float = 0.0
    genre_overlap_pct: float = 0.0
    theme_overlap_pct: float = 0.0
    director_match: bool = False
    actor_match_count: int = 0
    popularity: float = 0.0
    vote_average: float = 0.0
    vote_count: int = 0
    franchise_match: bool = False
    collection_match: bool = False
    runtime_similarity: float = 0.0
    release_year_distance: int = 100
    personalization_score: float = 0.0
    
    # Phase 8: Content Intelligence / Graph Features
    graph_similarity: float = 0.0
    graph_distance: int = 100
    shared_theme_score: float = 0.0
    shared_actor_score: float = 0.0
    shared_director_score: float = 0.0
    shared_keyword_score: float = 0.0

class Explainability(BaseModel):
    reason_codes: List[str] = Field(default_factory=list)
    reason_scores: Dict[str, float] = Field(default_factory=dict)

class RankingMetadata(BaseModel):
    rank: int
    recommendation_score: float
    confidence: float

class Recommendation(BaseModel):
    content_id: int
    ranking: RankingMetadata
    explainability: Explainability
    # Keeping raw features for debugging purposes
    features: Optional[FeatureVector] = None 

class DecisionDiagnostics(BaseModel):
    feature_extraction_ms: int = 0
    scoring_ms: int = 0
    diversity_ms: int = 0
    business_rules_ms: int = 0
    packaging_ms: int = 0
    total_ms: int = 0
    candidates_in: int = 0
    recommendations_out: int = 0
    duplicates_removed: int = 0
    diversity_replacements: int = 0
    business_rule_rejections: int = 0

class RecommendationPackage(BaseModel):
    schema_version: str = "1.0"
    recommendations: List[Recommendation]
    diagnostics: DecisionDiagnostics
