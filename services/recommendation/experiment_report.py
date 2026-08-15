"""
Streamora Recommendation Platform — Immutable Online Experiment Governance Reporter
Phase 7: Online Experimentation & Safe Model Deployment Platform

Generates reproducible immutable ML governance reports for production online experiments.
"""

from __future__ import annotations
import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

from services.recommendation.experiment_registry import ExperimentRecord
from services.recommendation.experiment_telemetry import VariantMetricSummary
from services.recommendation.guardrail_engine import GuardrailEvaluationReport
from services.recommendation.rollout_controller import RolloutDecisionPayload


@dataclass
class OnlineExperimentReport:
    """Immutable Production Online Experiment Governance Artifact."""
    report_id: str
    experiment_id: str
    experiment_layer: str
    control_model_version: str
    candidate_model_version: str
    dataset_version: str
    feature_snapshot_version: str
    phase6_4_certification_id: str
    final_state: str
    final_decision: str
    state_history: List[Dict[str, Any]]
    metrics_summary: Dict[str, Any]
    guardrail_report: Dict[str, Any]
    rollback_reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    certification_hash: str = ""

    def __post_init__(self):
        if not self.certification_hash:
            self.certification_hash = self.compute_hash()

    def compute_hash(self) -> str:
        payload = f"{self.report_id}:{self.experiment_id}:{self.final_state}:{self.candidate_model_version}:{self.phase6_4_certification_id}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "experiment_id": self.experiment_id,
            "experiment_layer": self.experiment_layer,
            "control_model_version": self.control_model_version,
            "candidate_model_version": self.candidate_model_version,
            "dataset_version": self.dataset_version,
            "feature_snapshot_version": self.feature_snapshot_version,
            "phase6_4_certification_id": self.phase6_4_certification_id,
            "final_state": self.final_state,
            "final_decision": self.final_decision,
            "state_history": self.state_history,
            "metrics_summary": self.metrics_summary,
            "guardrail_report": self.guardrail_report,
            "rollback_reason": self.rollback_reason,
            "created_at": self.created_at.isoformat(),
            "certification_hash": self.certification_hash,
        }


class ExperimentGovernanceReporter:
    """Factory for generating immutable Online Experiment Governance Reports."""

    @staticmethod
    def generate_report(
        record: ExperimentRecord,
        treatment_summary: VariantMetricSummary,
        control_summary: VariantMetricSummary,
        last_decision: RolloutDecisionPayload,
        total_catalog_size: int = 100
    ) -> OnlineExperimentReport:
        report_id = f"exp_rep_{uuid.uuid4().hex[:12]}"
        metrics_summary = {
            "treatment": treatment_summary.to_dict(total_catalog_size),
            "control": control_summary.to_dict(total_catalog_size),
            "deltas": {
                "ctr_relative_delta": round((treatment_summary.ctr - control_summary.ctr) / control_summary.ctr, 4) if control_summary.ctr > 0 else 0.0,
                "completion_rate_relative_delta": round((treatment_summary.completion_rate - control_summary.completion_rate) / control_summary.completion_rate, 4) if control_summary.completion_rate > 0 else 0.0,
                "error_rate_absolute_delta": round(treatment_summary.error_rate - control_summary.error_rate, 4),
            }
        }

        return OnlineExperimentReport(
            report_id=report_id,
            experiment_id=record.config.experiment_id,
            experiment_layer=record.config.experiment_layer,
            control_model_version=record.config.control_model_version,
            candidate_model_version=record.config.candidate_model_version,
            dataset_version=record.config.dataset_version,
            feature_snapshot_version=record.config.feature_snapshot_version,
            phase6_4_certification_id=record.config.phase6_4_certification_id,
            final_state=record.state.value,
            final_decision=last_decision.decision,
            state_history=record.state_history,
            metrics_summary=metrics_summary,
            guardrail_report=last_decision.guardrail_report.to_dict(),
            rollback_reason=record.rollback_reason,
        )
