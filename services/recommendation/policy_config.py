from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class RecommendationPolicy:
    """
    Configurable Signal Weight Policy for Recommendation Ranking.
    Allows runtime A/B testing and dynamic policy switching without code changes.
    """
    policy_name: str = "default_balanced"
    franchise_weight: float = 0.35
    universe_weight: float = 0.15
    studio_weight: float = 0.10
    graph_weight: float = 0.20
    genre_weight: float = 0.10
    mood_weight: float = 0.10
    cast_weight: float = 0.10
    director_weight: float = 0.08
    popularity_weight: float = 0.05
    collaborative_weight: float = 0.05

    @classmethod
    def get_preset_policy(cls, name: str = "default_balanced") -> RecommendationPolicy:
        if name == "universe_focused":
            return cls(
                policy_name="universe_focused",
                universe_weight=0.35,
                franchise_weight=0.25,
                graph_weight=0.20,
                studio_weight=0.10,
                genre_weight=0.10
            )
        elif name == "cast_spotlight_focused":
            return cls(
                policy_name="cast_spotlight_focused",
                cast_weight=0.40,
                director_weight=0.20,
                franchise_weight=0.20,
                studio_weight=0.10,
                genre_weight=0.10
            )
        return cls()
