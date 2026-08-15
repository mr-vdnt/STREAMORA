"""
Streamora Recommendation Platform — Guardrail Engine & Health Evaluator
Phase 7: Online Experimentation & Safe Model Deployment Platform

Implements sample-size reliability checks, absolute vs relative delta evaluations,
and automated guardrail breach detection.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from services.recommendation.experiment_telemetry import VariantMetricSummary


@dataclass
class GuardrailThresholds:
    """Configurable thresholds for production health guardrails."""
    min_treatment_exposures: int = 30
    min_control_exposures: int = 30
    min_outcomes: int = 10
    max_completion_relative_drop: float = 0.05   # 5% relative drop
    max_absolute_error_rate: float = 0.01          # 1% absolute error rate
    max_latency_p95_relative_increase: float = 0.20 # 20% relative latency spike
    min_absolute_catalog_coverage: float = 0.50    # 50% catalog coverage
    max_absolute_dislike_rate: float = 0.10        # 10% dislike rate


@dataclass
class GuardrailCheckResult:
    """Result of an individual guardrail check."""
    name: str
    passed: bool
    control_value: float
    treatment_value: float
    absolute_delta: float
    relative_delta: float
    threshold: float
    message: str


@dataclass
class GuardrailEvaluationReport:
    """Comprehensive Guardrail Evaluation Report."""
    overall_passed: bool
    status_code: str  # "PASSED" | "INSUFFICIENT_SAMPLE" | "GUARDRAIL_BREACHED"
    checks: List[GuardrailCheckResult] = field(default_factory=list)
    breached_guardrails: List[str] = field(default_factory=list)
    sample_size_passed: bool = True
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_passed": self.overall_passed,
            "status_code": self.status_code,
            "sample_size_passed": self.sample_size_passed,
            "reason": self.reason,
            "breached_guardrails": self.breached_guardrails,
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "control_value": round(c.control_value, 4),
                    "treatment_value": round(c.treatment_value, 4),
                    "absolute_delta": round(c.absolute_delta, 4),
                    "relative_delta": round(c.relative_delta, 4),
                    "threshold": c.threshold,
                    "message": c.message
                }
                for c in self.checks
            ]
        }


class GuardrailEngine:
    """Evaluates guardrails against treatment and control metric summaries."""

    def __init__(self, thresholds: Optional[GuardrailThresholds] = None):
        self.thresholds = thresholds or GuardrailThresholds()

    def evaluate(
        self,
        treatment: VariantMetricSummary,
        control: VariantMetricSummary,
        treatment_p95_latency_ms: float = 4.0,
        control_p95_latency_ms: float = 3.8,
        total_catalog_size: int = 100
    ) -> GuardrailEvaluationReport:
        t = self.thresholds

        # 1. Sample Size Reliability Gate
        total_outcomes = (treatment.clicks + treatment.detail_views + treatment.playback_starts)
        if (
            treatment.exposures < t.min_treatment_exposures
            or control.exposures < t.min_control_exposures
            or total_outcomes < t.min_outcomes
        ):
            return GuardrailEvaluationReport(
                overall_passed=True,
                status_code="INSUFFICIENT_SAMPLE",
                sample_size_passed=False,
                reason=(
                    f"Insufficient sample size: Treatment exposures={treatment.exposures} (min {t.min_treatment_exposures}), "
                    f"Control exposures={control.exposures} (min {t.min_control_exposures}), outcomes={total_outcomes} (min {t.min_outcomes})."
                )
            )

        checks: List[GuardrailCheckResult] = []
        breached: List[str] = []

        # 2. Completion Rate Drop (Relative)
        c_ctrl = control.completion_rate
        c_trt = treatment.completion_rate
        abs_comp = c_trt - c_ctrl
        rel_comp = (abs_comp / c_ctrl) if c_ctrl > 0 else 0.0
        comp_passed = rel_comp >= -t.max_completion_relative_drop
        checks.append(GuardrailCheckResult(
            name="completion_rate_drop",
            passed=comp_passed,
            control_value=c_ctrl,
            treatment_value=c_trt,
            absolute_delta=abs_comp,
            relative_delta=rel_comp,
            threshold=-t.max_completion_relative_drop,
            message=f"Relative completion rate change: {rel_comp*100:.2f}% (max allowed drop: -{t.max_completion_relative_drop*100:.1f}%)"
        ))
        if not comp_passed:
            breached.append("completion_rate_drop")

        # 3. Error Rate Spike (Absolute)
        e_ctrl = control.error_rate
        e_trt = treatment.error_rate
        abs_err = e_trt - e_ctrl
        rel_err = (abs_err / e_ctrl) if e_ctrl > 0 else 0.0
        err_passed = e_trt <= t.max_absolute_error_rate
        checks.append(GuardrailCheckResult(
            name="error_rate_spike",
            passed=err_passed,
            control_value=e_ctrl,
            treatment_value=e_trt,
            absolute_delta=abs_err,
            relative_delta=rel_err,
            threshold=t.max_absolute_error_rate,
            message=f"Treatment error rate: {e_trt*100:.2f}% (max allowed: {t.max_absolute_error_rate*100:.1f}%)"
        ))
        if not err_passed:
            breached.append("error_rate_spike")

        # 4. Latency P95 Spike (Relative)
        abs_lat = treatment_p95_latency_ms - control_p95_latency_ms
        rel_lat = (abs_lat / control_p95_latency_ms) if control_p95_latency_ms > 0 else 0.0
        lat_passed = rel_lat <= t.max_latency_p95_relative_increase
        checks.append(GuardrailCheckResult(
            name="latency_p95_spike",
            passed=lat_passed,
            control_value=control_p95_latency_ms,
            treatment_value=treatment_p95_latency_ms,
            absolute_delta=abs_lat,
            relative_delta=rel_lat,
            threshold=t.max_latency_p95_relative_increase,
            message=f"P95 latency change: +{rel_lat*100:.1f}% (max allowed increase: +{t.max_latency_p95_relative_increase*100:.0f}%)"
        ))
        if not lat_passed:
            breached.append("latency_p95_spike")

        # 5. Catalog Coverage Drop (Absolute)
        cov_ctrl = control.catalog_coverage(total_catalog_size)
        cov_trt = treatment.catalog_coverage(total_catalog_size)
        abs_cov = cov_trt - cov_ctrl
        rel_cov = (abs_cov / cov_ctrl) if cov_ctrl > 0 else 0.0
        cov_passed = cov_trt >= t.min_absolute_catalog_coverage
        checks.append(GuardrailCheckResult(
            name="catalog_coverage_drop",
            passed=cov_passed,
            control_value=cov_ctrl,
            treatment_value=cov_trt,
            absolute_delta=abs_cov,
            relative_delta=rel_cov,
            threshold=t.min_absolute_catalog_coverage,
            message=f"Treatment catalog coverage: {cov_trt*100:.1f}% (minimum required: {t.min_absolute_catalog_coverage*100:.0f}%)"
        ))
        if not cov_passed:
            breached.append("catalog_coverage_drop")

        # 6. Dislike Rate Spike (Absolute)
        d_ctrl = control.dislike_rate
        d_trt = treatment.dislike_rate
        abs_dislike = d_trt - d_ctrl
        rel_dislike = (abs_dislike / d_ctrl) if d_ctrl > 0 else 0.0
        dislike_passed = d_trt <= t.max_absolute_dislike_rate
        checks.append(GuardrailCheckResult(
            name="dislike_rate_spike",
            passed=dislike_passed,
            control_value=d_ctrl,
            treatment_value=d_trt,
            absolute_delta=abs_dislike,
            relative_delta=rel_dislike,
            threshold=t.max_absolute_dislike_rate,
            message=f"Treatment dislike rate: {d_trt*100:.1f}% (max allowed: {t.max_absolute_dislike_rate*100:.0f}%)"
        ))
        if not dislike_passed:
            breached.append("dislike_rate_spike")

        overall_passed = len(breached) == 0
        status_code = "PASSED" if overall_passed else "GUARDRAIL_BREACHED"
        reason = "All guardrails passed cleanly." if overall_passed else f"Guardrails breached: {', '.join(breached)}"

        return GuardrailEvaluationReport(
            overall_passed=overall_passed,
            status_code=status_code,
            checks=checks,
            breached_guardrails=breached,
            sample_size_passed=True,
            reason=reason
        )
