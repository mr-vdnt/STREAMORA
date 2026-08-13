"""
Recommendation Feature Store for Streamora Phase 5.

Decouples event telemetry and catalog metadata from candidate generation and LTR ranking.
Maintains feature vectors for Users and Content Items:
- User Features: genre_affinity, theme_affinity, director_affinity, recency_decay.
- Content Features: popularity_score, canonical_rating, release_year, freshness_score, engagement_stats.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any


@dataclass
class UserFeatureVector:
    user_id: str
    genre_affinity: Dict[str, float] = field(default_factory=dict)
    theme_affinity: Dict[str, float] = field(default_factory=dict)
    director_affinity: Dict[str, float] = field(default_factory=dict)
    interaction_count: int = 0
    last_active: Optional[datetime] = None


@dataclass
class ContentFeatureVector:
    content_id: int
    popularity_score: float = 0.0
    canonical_rating: float = 0.0
    vote_count: int = 0
    release_year: Optional[int] = None
    freshness_score: float = 1.0
    completion_rate: float = 0.0
    like_ratio: float = 0.0


class RecommendationFeatureStore:
    """In-memory & persistent feature store for recommendation features."""

    def __init__(self):
        self._user_features: Dict[str, UserFeatureVector] = {}
        self._content_features: Dict[int, ContentFeatureVector] = {}

    def get_user_features(self, user_id: str) -> UserFeatureVector:
        if user_id not in self._user_features:
            self._user_features[user_id] = UserFeatureVector(user_id=user_id)
        return self._user_features[user_id]

    def set_user_features(self, vector: UserFeatureVector) -> None:
        self._user_features[vector.user_id] = vector

    def get_content_features(self, content_id: int) -> ContentFeatureVector:
        if content_id not in self._content_features:
            self._content_features[content_id] = ContentFeatureVector(content_id=content_id)
        return self._content_features[content_id]

    def set_content_features(self, vector: ContentFeatureVector) -> None:
        self._content_features[vector.content_id] = vector
