"""
Shadow Deployment Mode & A/B Experiment Manager for Streamora Phase 6.

Evaluates shadow model predictions alongside production model without affecting user slates.
Computes shadow divergence and offline metric comparisons.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any
from services.recommendation.model_registry import ModelRegistry, ModelArtifact
from services.recommendation.learned_ltr import LearnedLTREngine


@dataclass
class ShadowEvaluationLog:
    user_id: str
    active_version: str
    active_slate_ids: List[int]
    shadow_version: str
    shadow_slate_ids: List[int]
    divergence_ratio: float


class ShadowExperimentRunner:
    """Executes shadow model predictions alongside production models."""

    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self.shadow_logs: List[ShadowEvaluationLog] = []

    def evaluate_shadow(
        self, user_id: str, target_item: Dict[str, Any], catalog: List[Dict[str, Any]], active_slate: List[Dict[str, Any]]
    ) -> ShadowEvaluationLog:
        active_art = self.registry.get_active_model()
        shadow_art = self.registry.get_shadow_model()

        active_ver = active_art.version if active_art else "active-v5.1"
        shadow_ver = shadow_art.version if shadow_art else "shadow-v6.0"

        active_ids = [x["id"] for x in active_slate]

        # Predict using shadow model weights
        shadow_engine = LearnedLTREngine(version=shadow_ver)
        if shadow_art:
            shadow_engine.feature_weights = shadow_art.weights

        shadow_scored = []
        for item in catalog:
            features = {
                "user_affinity": 0.85 if "Sci-Fi" in item.get("genres", []) else 0.50,
                "collaborative_score": 0.80 if item.get("popularity", 0) > 80 else 0.40,
                "graph_sim": 0.90 if item.get("director") == target_item.get("director") else 0.30
            }
            score = shadow_engine.predict_item_score(features)
            item_c = item.copy()
            item_c["shadow_score"] = score
            shadow_scored.append(item_c)

        shadow_scored.sort(key=lambda x: x["shadow_score"], reverse=True)
        shadow_ids = [x["id"] for x in shadow_scored[:len(active_slate)]]

        # Calculate slate divergence ratio
        overlap = len(set(active_ids).intersection(set(shadow_ids)))
        divergence = 1.0 - (overlap / float(max(1, len(active_ids))))

        log = ShadowEvaluationLog(
            user_id=user_id,
            active_version=active_ver,
            active_slate_ids=active_ids,
            shadow_version=shadow_ver,
            shadow_slate_ids=shadow_ids,
            divergence_ratio=round(divergence, 4)
        )

        self.shadow_logs.append(log)
        return log
