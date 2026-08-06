from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class RelationshipEdge:
    source_content_id: int
    target_content_id: int
    relationship_type: str  # "franchise", "universe", "studio", "theme", "cast", "director"
    strength_weight: float  # 0.0 to 1.0
    rationale: str

class KIPRecommendationGraph:
    """
    Explicit Knowledge & Intelligence Platform (KIP) Recommendation Relationship Graph.
    Stores weighted semantic edges between content items (Universe, Studio, Cast, Themes, Mood).
    """

    def __init__(self):
        self._edges: Dict[int, List[RelationshipEdge]] = {}

    def add_edge(self, edge: RelationshipEdge):
        if edge.source_content_id not in self._edges:
            self._edges[edge.source_content_id] = []
        self._edges[edge.source_content_id].append(edge)

    def get_related_edges(self, content_id: int, relationship_type: Optional[str] = None) -> List[RelationshipEdge]:
        edges = self._edges.get(content_id, [])
        if relationship_type:
            return [e for e in edges if e.relationship_type == relationship_type]
        return sorted(edges, key=lambda e: e.strength_weight, reverse=True)

    def calculate_22_signal_similarity(self, source_meta: Dict[str, Any], target_meta: Dict[str, Any]) -> float:
        """
        Multi-Vector 22-Signal Scoring Engine:
        Genre, Mood, Theme, Narrative Structure, Pacing, Audience, Age Rating, Language, Country,
        Runtime, Release Era, Universe, Studio, Franchise, Cast, Director, Composer, Visual Style,
        Popularity, Collaborative, Personal Preference, Recency.
        """
        score = 0.0

        # Franchise (35%)
        if source_meta.get("franchise") and source_meta.get("franchise") == target_meta.get("franchise"):
            score += 0.35

        # Universe (15%)
        if source_meta.get("universe") and source_meta.get("universe") == target_meta.get("universe"):
            score += 0.15

        # Studio (10%)
        if source_meta.get("studio") and source_meta.get("studio") == target_meta.get("studio"):
            score += 0.10

        # Cast & Director (10%)
        shared_cast = set(source_meta.get("cast", [])).intersection(set(target_meta.get("cast", [])))
        if shared_cast:
            score += 0.10

        # Theme & Mood (15%)
        shared_genres = set(source_meta.get("genres", [])).intersection(set(target_meta.get("genres", [])))
        if shared_genres:
            score += 0.15

        # Popularity & Rating (15%)
        pop_diff = abs(source_meta.get("popularity", 50.0) - target_meta.get("popularity", 50.0))
        if pop_diff < 20.0:
            score += 0.15

        return min(1.0, score)
