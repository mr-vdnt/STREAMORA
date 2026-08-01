from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

@dataclass
class UserIntelligenceProfileDTO:
    user_id: str
    genre_affinities: Dict[str, float] = field(default_factory=dict)
    theme_affinities: Dict[str, float] = field(default_factory=dict)
    mood_affinities: Dict[str, float] = field(default_factory=dict)
    person_affinities: Dict[str, float] = field(default_factory=dict)
    franchise_affinities: Dict[str, float] = field(default_factory=dict)
    language_affinities: Dict[str, float] = field(default_factory=dict)
    runtime_preference: str = "standard"
    freshness_preference: float = 0.5
    novelty_preference: float = 0.5
    popularity_bias: float = 0.5
    completion_rate: float = 0.8
    total_searches: int = 0
    total_watches: int = 0

@dataclass
class RecommendationPlanDTO:
    user_id: str
    slate_type: str  # SlateType value
    context_item_id: Optional[int] = None
    target_genres: List[str] = field(default_factory=list)
    target_moods: List[str] = field(default_factory=list)
    active_generators: List[str] = field(default_factory=list)
    allocated_counts: Dict[str, int] = field(default_factory=dict)
    estimated_cost: float = 1.0
    latency_budget_ms: float = 80.0
    plan_hash: str = ""

@dataclass
class RecommendationCandidateDTO:
    content_id: int
    generator_name: str
    score: float
    reason: str
    provenance_metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RecommendationItemDTO:
    content_id: int
    title: str
    slug: str
    entity_type: str
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    rating: float = 0.0
    popularity: float = 0.0
    score: float = 0.0
    matched_sources: List[str] = field(default_factory=list)
    explanation: Optional[str] = None

@dataclass
class ShelfDTO:
    title: str
    slate_type: str
    items: List[RecommendationItemDTO] = field(default_factory=list)

@dataclass
class HomeFeedDTO:
    user_id: str
    shelves: List[ShelfDTO] = field(default_factory=list)
    latency_ms: float = 0.0
