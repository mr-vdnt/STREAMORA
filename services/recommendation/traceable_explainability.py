"""
Recommendation Traceability & Explainability Payload Generator for Streamora Phase 5.

Generates fine-grained, observable recommendation tracing payloads for debugging,
feature attribution, and user-facing explainability.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class RecommendationTracePayload:
    item_id: int
    rank: int
    score: float
    model_version: str
    candidate_sources: List[str]
    features: Dict[str, float]
    reason: Dict[str, str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "rank": self.rank,
            "score": round(self.score, 4),
            "model_version": self.model_version,
            "candidate_sources": self.candidate_sources,
            "features": {k: round(v, 4) for k, v in self.features.items()},
            "reason": self.reason
        }


class RecommendationTraceabilityEngine:
    """Converts recommendation candidate fusion outputs into observable traceability records."""

    def __init__(self, model_version: str = "hybrid-ranker-v5.0"):
        self.model_version = model_version

    def build_trace(self, item: Dict[str, Any], rank: int) -> RecommendationTracePayload:
        signals = item.get("fusion_signals", [])
        sources = list({s.get("type", "unknown") for s in signals}) if signals else ["baseline_popular"]
        
        primary_rationale = item.get("rationale", "✓ Recommended for You")
        
        features = {
            "user_affinity": item.get("rank_score", 0.50),
            "freshness": item.get("freshness_score", 1.0),
            "base_candidate_strength": signals[0].get("strength", 0.80) if signals else 0.50
        }

        return RecommendationTracePayload(
            item_id=item.get("id", 0),
            rank=rank,
            score=item.get("rank_score", 0.50),
            model_version=self.model_version,
            candidate_sources=sources,
            features=features,
            reason={
                "type": sources[0] if sources else "popularity",
                "label": primary_rationale
            }
        )
