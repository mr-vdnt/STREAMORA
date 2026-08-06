from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any

@dataclass
class LTRFeatureVector:
    content_id: int
    graph_sim: float = 0.0
    vector_sim: float = 0.0
    freshness_decay: float = 1.0
    popularity: float = 0.0
    completion_rate: float = 0.0
    actor_affinity: float = 0.0
    genre_affinity: float = 0.0
    session_sim: float = 0.0
    language_affinity: float = 1.0
    era_affinity: float = 1.0
    negative_penalty: float = 0.0
    user_affinity: float = 0.0

class LearningToRankEngine:
    """
    Learning-to-Rank (LTR) Machine-Learned Feature Vector Ranker.
    Combines 12 multi-dimensional feature signals into a predictive ranking score.
    """

    def __init__(self):
        # Learned model weights (simulated XGBoost/LightGBM tree weights)
        self.weights = {
            "graph_sim": 0.25,
            "vector_sim": 0.20,
            "freshness_decay": 0.15,
            "popularity": 0.10,
            "genre_affinity": 0.10,
            "actor_affinity": 0.08,
            "session_sim": 0.07,
            "completion_rate": 0.05
        }

    def predict_score(self, fv: LTRFeatureVector) -> float:
        score = (
            fv.graph_sim * self.weights["graph_sim"] +
            fv.vector_sim * self.weights["vector_sim"] +
            fv.freshness_decay * self.weights["freshness_decay"] +
            (fv.popularity / 100.0) * self.weights["popularity"] +
            fv.genre_affinity * self.weights["genre_affinity"] +
            fv.actor_affinity * self.weights["actor_affinity"] +
            fv.session_sim * self.weights["session_sim"] +
            fv.completion_rate * self.weights["completion_rate"] -
            fv.negative_penalty
        )
        return max(0.0, score)

    def rank_candidates(self, candidate_feature_vectors: List[LTRFeatureVector]) -> List[Dict[str, Any]]:
        scored = []
        for fv in candidate_feature_vectors:
            score = self.predict_score(fv)
            scored.append({"content_id": fv.content_id, "ltr_score": score})
        return sorted(scored, key=lambda x: x["ltr_score"], reverse=True)
