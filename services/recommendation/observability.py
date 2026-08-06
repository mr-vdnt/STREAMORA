from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class PipelineLatencyBreakdown:
    vector_retrieval_ms: float = 0.0
    graph_retrieval_ms: float = 0.0
    candidate_merge_ms: float = 0.0
    ltr_ranking_ms: float = 0.0
    diversification_ms: float = 0.0
    total_pipeline_ms: float = 0.0

class RetrievalObservabilityTracker:
    """
    Stage-Level Retrieval & Recommendation Pipeline Latency Observability Tracker.
    Records microsecond-level execution breakdown across candidate generation and ML ranking stages.
    """

    def __init__(self):
        self._breakdown = PipelineLatencyBreakdown()

    def record_stage(self, stage_name: str, duration_ms: float):
        if hasattr(self._breakdown, f"{stage_name}_ms"):
            setattr(self._breakdown, f"{stage_name}_ms", round(duration_ms, 2))

    def get_summary(self) -> Dict[str, Any]:
        return {
            "vector_retrieval_ms": self._breakdown.vector_retrieval_ms,
            "graph_retrieval_ms": self._breakdown.graph_retrieval_ms,
            "candidate_merge_ms": self._breakdown.candidate_merge_ms,
            "ltr_ranking_ms": self._breakdown.ltr_ranking_ms,
            "diversification_ms": self._breakdown.diversification_ms,
            "total_pipeline_ms": self._breakdown.total_pipeline_ms
        }
