"""
Streamora Recommendation Platform — Progressive Rollout Controller & State Machine
Phase 7: Online Experimentation & Safe Model Deployment Platform

Implements progressive multi-stage rollout state machine transitions with optimistic concurrency control,
automated guardrail evaluation, and instant zero-downtime emergency rollback.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

from services.recommendation.experiment_registry import (
    ExperimentLifecycleState,
    ExperimentRecord,
    ExperimentRegistry,
)
from services.recommendation.experiment_telemetry import (
    ExperimentTelemetryCollector,
    VariantMetricSummary,
)
from services.recommendation.guardrail_engine import (
    GuardrailEngine,
    GuardrailEvaluationReport,
)


@dataclass
class RolloutDecisionPayload:
    """Decision payload returned by progressive rollout evaluation."""
    experiment_id: str
    decision: str  # "ADVANCE" | "HOLD" | "ROLLBACK" | "NO_OP"
    previous_stage: str
    current_stage: str
    version: int
    guardrail_report: GuardrailEvaluationReport
    reason: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "decision": self.decision,
            "previous_stage": self.previous_stage,
            "current_stage": self.current_stage,
            "version": self.version,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            "guardrail_report": self.guardrail_report.to_dict()
        }


STAGE_ORDER: List[ExperimentLifecycleState] = [
    ExperimentLifecycleState.SHADOW,
    ExperimentLifecycleState.STAGE_5PCT,
    ExperimentLifecycleState.STAGE_10PCT,
    ExperimentLifecycleState.STAGE_25PCT,
    ExperimentLifecycleState.STAGE_50PCT,
    ExperimentLifecycleState.PROMOTED_100PCT,
]


class ProgressiveRolloutController:
    """Controller managing automated multi-stage progressive deployments and emergency rollbacks."""

    def __init__(
        self,
        registry: ExperimentRegistry,
        telemetry: ExperimentTelemetryCollector,
        guardrail_engine: Optional[GuardrailEngine] = None
    ):
        self.registry = registry
        self.telemetry = telemetry
        self.guardrail_engine = guardrail_engine or GuardrailEngine()

    def _get_next_stage(self, current: ExperimentLifecycleState) -> Optional[ExperimentLifecycleState]:
        if current not in STAGE_ORDER:
            return None
        idx = STAGE_ORDER.index(current)
        if idx < len(STAGE_ORDER) - 1:
            return STAGE_ORDER[idx + 1]
        return None

    def evaluate_and_step(
        self,
        experiment_id: str,
        treatment_p95_ms: float = 4.0,
        control_p95_ms: float = 3.8
    ) -> RolloutDecisionPayload:
        record = self.registry.get_experiment(experiment_id)
        if not record:
            raise KeyError(f"Experiment {experiment_id} not registered.")

        prev_stage = record.state.value

        # Inactive or terminal states
        if record.state in [ExperimentLifecycleState.ROLLED_BACK, ExperimentLifecycleState.TERMINATED, ExperimentLifecycleState.PROMOTED_100PCT]:
            summaries = self.telemetry.get_summary(experiment_id)
            report = self.guardrail_engine.evaluate(
                summaries["TREATMENT"], summaries["CONTROL"],
                treatment_p95_latency_ms=treatment_p95_ms,
                control_p95_latency_ms=control_p95_ms
            )
            return RolloutDecisionPayload(
                experiment_id=experiment_id,
                decision="NO_OP",
                previous_stage=prev_stage,
                current_stage=prev_stage,
                version=record.version,
                guardrail_report=report,
                reason=f"Experiment in terminal state {prev_stage}; no transition possible."
            )

        if record.state == ExperimentLifecycleState.READY:
            # Start shadow evaluation phase
            updated = self.registry.update_state_atomic(
                experiment_id=experiment_id,
                expected_version=record.version,
                new_state=ExperimentLifecycleState.SHADOW,
                reason="Initiating Shadow Evaluation Phase"
            )
            summaries = self.telemetry.get_summary(experiment_id)
            report = self.guardrail_engine.evaluate(
                summaries["TREATMENT"], summaries["CONTROL"],
                treatment_p95_latency_ms=treatment_p95_ms,
                control_p95_latency_ms=control_p95_ms
            )
            return RolloutDecisionPayload(
                experiment_id=experiment_id,
                decision="ADVANCE",
                previous_stage=prev_stage,
                current_stage=updated.state.value,
                version=updated.version,
                guardrail_report=report,
                reason="Promoted from READY to SHADOW mode."
            )

        # Active stage evaluation
        summaries = self.telemetry.get_summary(experiment_id)
        report = self.guardrail_engine.evaluate(
            summaries["TREATMENT"],
            summaries["CONTROL"],
            treatment_p95_latency_ms=treatment_p95_ms,
            control_p95_latency_ms=control_p95_ms
        )

        # 1. Guardrail Breach -> Immediate Atomic Rollback
        if report.status_code == "GUARDRAIL_BREACHED":
            updated = self.registry.update_state_atomic(
                experiment_id=experiment_id,
                expected_version=record.version,
                new_state=ExperimentLifecycleState.ROLLED_BACK,
                reason=f"Emergency Rollback: {report.reason}"
            )
            return RolloutDecisionPayload(
                experiment_id=experiment_id,
                decision="ROLLBACK",
                previous_stage=prev_stage,
                current_stage=updated.state.value,
                version=updated.version,
                guardrail_report=report,
                reason=f"Emergency rollback triggered: {report.reason}"
            )

        # 2. Insufficient Sample -> Hold Current Stage
        if report.status_code == "INSUFFICIENT_SAMPLE":
            return RolloutDecisionPayload(
                experiment_id=experiment_id,
                decision="HOLD",
                previous_stage=prev_stage,
                current_stage=prev_stage,
                version=record.version,
                guardrail_report=report,
                reason=report.reason
            )

        # 3. All Guardrails Passed -> Advance to Next Progressive Stage
        next_stage = self._get_next_stage(record.state)
        if next_stage:
            updated = self.registry.update_state_atomic(
                experiment_id=experiment_id,
                expected_version=record.version,
                new_state=next_stage,
                reason=f"Advanced from {record.state.value} to {next_stage.value} based on clean guardrail evaluation."
            )
            return RolloutDecisionPayload(
                experiment_id=experiment_id,
                decision="ADVANCE",
                previous_stage=prev_stage,
                current_stage=updated.state.value,
                version=updated.version,
                guardrail_report=report,
                reason=f"Successfully advanced from {prev_stage} to {updated.state.value}."
            )

        return RolloutDecisionPayload(
            experiment_id=experiment_id,
            decision="NO_OP",
            previous_stage=prev_stage,
            current_stage=prev_stage,
            version=record.version,
            guardrail_report=report,
            reason="Experiment already at maximum stage."
        )
