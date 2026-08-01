from __future__ import annotations
import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List
from services.knowledge.dtos import KnowledgeFactDTO, IntelligenceProfileDTO, KnowledgeSnapshotDTO
from services.knowledge.engines.summary_builder import SummaryBuilder

class ProfileMaterializer:
    """
    Asynchronously materializes CQRS IntelligenceProfile read views and KnowledgeSnapshots from active facts.
    """

    def __init__(self):
        self.summary_builder = SummaryBuilder()

    def generate_snapshot_hash(self, facts: List[KnowledgeFactDTO]) -> str:
        """Computes deterministic SHA-256 hash of active facts for snapshot reproducibility."""
        sorted_fact_strings = sorted([
            f"{f.category}:{f.predicate}:{f.value}:{f.confidence:.2f}:{f.source_weight:.2f}"
            for f in facts if f.state == "ACTIVE"
        ])
        raw = "|".join(sorted_fact_strings)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def materialize(
        self, 
        content_id: int, 
        content_data: Dict[str, Any], 
        facts: List[KnowledgeFactDTO]
    ) -> IntelligenceProfileDTO:
        active_facts = [f for f in facts if f.state == "ACTIVE"]

        themes = list(dict.fromkeys([f.value for f in active_facts if f.category == "theme"]))
        moods = list(dict.fromkeys([f.value for f in active_facts if f.category == "mood"]))
        warnings = list(dict.fromkeys([f.value.replace("warning-", "") for f in active_facts if f.category == "audience_safety" and "warning-" in f.value]))

        pacing_fact = next((f.value.replace("pacing-", "") for f in active_facts if "pacing-" in f.value), "steady")
        rating_fact = next((f.value.replace("rating-", "") for f in active_facts if "rating-" in f.value), "PG-13")
        structure_fact = next((f.value.replace("structure-", "") for f in active_facts if "structure-" in f.value), "linear")

        summaries = self.summary_builder.build_summaries(content_data, active_facts)

        # Compute overall confidence (weighted average)
        if active_facts:
            overall_conf = sum(f.confidence * f.source_weight for f in active_facts) / sum(f.source_weight for f in active_facts)
        else:
            overall_conf = 1.0

        return IntelligenceProfileDTO(
            content_id=content_id,
            profile_version="1.0.0",
            dominant_themes=themes,
            dominant_moods=moods,
            pacing=pacing_fact,
            narrative_structure=structure_fact,
            audience_rating=rating_fact,
            content_warnings=warnings,
            summary_short=summaries["summary_short"],
            summary_medium=summaries["summary_medium"],
            summary_deep=summaries["summary_deep"],
            summary_spoiler_free=summaries["summary_spoiler_free"],
            overall_confidence=round(overall_conf, 2),
            fact_count=len(active_facts)
        )
