from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class ExperimentVariant:
    variant_id: str
    policy_name: str
    description: str

class ExperimentManager:
    """
    Online A/B Experiment & Variant Manager.
    Hashes user_id into experiment variants and tracks impression/click metrics.
    """

    def __init__(self):
        self.variants = {
            "variant_a": ExperimentVariant("variant_a", "default_balanced", "Baseline Balanced Policy"),
            "variant_b": ExperimentVariant("variant_b", "universe_focused", "MCU/DCU Universe Focused Policy"),
            "variant_c": ExperimentVariant("variant_c", "cast_spotlight_focused", "Cast & Crew Spotlight Policy")
        }
        self.metrics: Dict[str, Dict[str, int]] = {v: {"impressions": 0, "clicks": 0} for v in self.variants}

    def assign_variant(self, user_id: str) -> ExperimentVariant:
        hash_val = int(hashlib.md5(user_id.encode("utf-8")).hexdigest(), 16)
        buckets = list(self.variants.keys())
        idx = hash_val % len(buckets)
        return self.variants[buckets[idx]]

    def record_impression(self, variant_id: str):
        if variant_id in self.metrics:
            self.metrics[variant_id]["impressions"] += 1

    def record_click(self, variant_id: str):
        if variant_id in self.metrics:
            self.metrics[variant_id]["clicks"] += 1

    def get_ctr(self, variant_id: str) -> float:
        m = self.metrics.get(variant_id, {"impressions": 0, "clicks": 0})
        if m["impressions"] == 0:
            return 0.0
        return (m["clicks"] / m["impressions"]) * 100.0
