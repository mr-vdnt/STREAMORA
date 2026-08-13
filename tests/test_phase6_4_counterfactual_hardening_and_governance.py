"""
Phase 6.4 Master Certification Test Suite: Counterfactual Evaluation Hardening & Governance Certification.

Validates:
1. Paired Request Bootstrap resampling on EvaluationContext units (1 request_id = 1 unit).
2. Dual ESS & ESS-Ratio Promotion Gates (ESS >= ESS_min AND ESS/N >= rho_min).
3. Action-Support Coverage (Coverage >= C_min) metric calculation & gate enforcement.
4. Complete Propensity Diagnostic Engine emission (P50/P95/P99, weight variance, clipping fraction).
5. Immutable Production Governance ML Certification Artifact (PolicyAwareCertification) with machine-readable codes.
"""
from datetime import datetime, timezone
import math
import pytest
from services.recommendation.exposure_logger import ExposureRecord, ExposureLogEntry
from services.recommendation.counterfactual_evaluator import (
    CounterfactualEvaluator,
    PolicyAwarePromotionGate,
    PropensityDiagnosticEngine,
    EvaluationContext,
    PolicyAwareCertification,
    GovernanceRejectionCode
)


def test_evaluation_context_and_paired_bootstrap_covariance():
    """Verify paired bootstrap resamples EvaluationContext units by request_id, preserving covariance."""
    gate = PolicyAwarePromotionGate(min_ess=1.0, min_ess_ratio=0.01)

    now = datetime.now(timezone.utc)
    cand_records = [
        ExposureRecord("e1", "req1", "u1", 11, 1, "s1", "v6.3", "cand-v6.4", 0.90, 0.85, 1.00, 0.90, now, "completion"),
        ExposureRecord("e2", "req2", "u2", 12, 2, "s2", "v6.3", "cand-v6.4", 0.90, 0.85, 0.707, 0.636, now, "like"),
        ExposureRecord("e3", "req3", "u3", 13, 1, "s3", "v6.3", "cand-v6.4", 0.90, 0.85, 1.00, 0.90, now, "watchlist"),
        ExposureRecord("e4", "req4", "u4", 14, 5, "s4", "v6.3", "cand-v6.4", 0.90, 0.85, 0.447, 0.402, now, "playback_start"),
        ExposureRecord("e5", "req5", "u5", 15, 3, "s5", "v6.3", "cand-v6.4", 0.90, 0.85, 0.577, 0.519, now, "click")
    ]

    ctrl_records = [
        ExposureRecord("e10", "req1", "u1", 11, 1, "s1", "v6.3", "ctrl-v6.3", 0.90, 0.85, 1.00, 0.90, now, "click"),
        ExposureRecord("e20", "req2", "u2", 12, 2, "s2", "v6.3", "ctrl-v6.3", 0.90, 0.85, 0.707, 0.636, now, None),
        ExposureRecord("e30", "req3", "u3", 13, 1, "s3", "v6.3", "ctrl-v6.3", 0.90, 0.85, 1.00, 0.90, now, "click"),
        ExposureRecord("e40", "req4", "u4", 14, 5, "s4", "v6.3", "ctrl-v6.3", 0.90, 0.85, 0.447, 0.402, now, None),
        ExposureRecord("e50", "req5", "u5", 15, 3, "s5", "v6.3", "ctrl-v6.3", 0.90, 0.85, 0.577, 0.519, now, None)
    ]

    contexts, rejections = gate.build_evaluation_contexts(cand_records, ctrl_records)
    assert len(contexts) == 5
    assert len(rejections) == 0

    paired_boot = gate.paired_bootstrap_delta_snips(contexts, num_bootstrap_samples=100, seed=42)
    assert paired_boot["delta_mean"] > 0.0
    assert paired_boot["ci_lower"] > 0.0
    assert paired_boot["ci_upper"] >= paired_boot["ci_lower"]
    assert len(paired_boot["deltas"]) == 100


def test_dual_ess_and_ess_ratio_promotion_gate():
    """Verify dual ESS criteria (ESS >= min_ess AND ESS/N >= min_ess_ratio) correctly rejects low-ratio candidate pools."""
    gate = PolicyAwarePromotionGate(min_ess=2.0, min_ess_ratio=0.95)

    now = datetime.now(timezone.utc)
    cand_records = []
    for i in range(10):
        rank = 1 if i < 2 else 20
        cand_records.append(
            ExposureRecord(f"cand-{i}", f"req-{i}", f"u-{i}", 10+i, rank, "s", "v6.3", "cand-v6.4", 0.90, 0.85, 1.0/math.sqrt(rank), 0.90/math.sqrt(rank), now, "completion")
        )

    ctrl_records = [
        ExposureRecord(f"ctrl-{i}", f"req-{i}", f"u-{i}", 10+i, 1, "s", "v6.3", "ctrl-v6.3", 0.90, 0.85, 1.0, 0.90, now, "click")
        for i in range(10)
    ]

    cert = gate.certify_policy_promotion(
        candidate_version="cand-v6.4",
        control_version="ctrl-v6.3",
        candidate_records=cand_records,
        control_records=ctrl_records
    )

    assert cert.is_approved is False
    reason_codes = [r["code"] for r in cert.decision["reasons"]]
    assert GovernanceRejectionCode.INSUFFICIENT_ESS_RATIO in reason_codes


def test_propensity_diagnostic_engine_completeness():
    """Verify PropensityDiagnosticEngine emits complete weight percentiles, variance, and clipping metrics."""
    weights = [0.94, 1.20, 2.50, 4.10, 10.0, 10.0]
    propensities = [0.90, 0.70, 0.50, 0.30, 0.10, 0.05]

    diag = PropensityDiagnosticEngine.compute_diagnostics(weights, propensities, clip_max=10.0)

    assert diag["sample_count"] == 6
    assert diag["effective_sample_size"] > 0.0
    assert 0.0 < diag["ess_ratio"] <= 1.0
    assert diag["weight_mean"] > 0.0
    assert diag["weight_variance"] > 0.0
    assert diag["weight_p50"] > 0.0
    assert diag["weight_p95"] > 0.0
    assert diag["weight_p99"] > 0.0
    assert diag["weight_max"] == 10.0
    assert diag["clipped_weight_count"] == 2
    assert diag["clipped_weight_fraction"] == round(2.0 / 6.0, 4)
    assert diag["propensity_min"] == 0.05
    assert diag["propensity_median"] > 0.0


def test_formal_action_support_coverage_calculation():
    """Verify formal support coverage metric calculation and gate rejection when coverage < 50%."""
    gate = PolicyAwarePromotionGate(min_support_coverage=0.50)

    now = datetime.now(timezone.utc)
    cand_records = [
        ExposureRecord("e1", "req1", "u1", 11, 1, "s1", "v6.3", "cand-v6.4", 0.90, 0.85, 1.0, 0.90, now, "completion"),
        ExposureRecord("e2", "req2", "u2", 12, 2, "s2", "v6.3", "cand-v6.4", 0.90, 0.85, 0.7, 0.63, now, "like"),
        ExposureRecord("e3", "req3", "u3", 13, 1, "s3", "v6.3", "cand-v6.4", 0.00, 0.85, 1.0, 0.00, now, "watchlist"),
        ExposureRecord("e4", "req4", "u4", 14, 5, "s4", "v6.3", "cand-v6.4", 0.00, 0.85, 0.4, 0.00, now, "playback_start"),
        ExposureRecord("e5", "req5", "u5", 15, 3, "s5", "v6.3", "cand-v6.4", 0.00, 0.85, 0.5, 0.00, now, "click")
    ]

    ctrl_records = [
        ExposureRecord(f"c-{i}", f"req{i+1}", f"u{i+1}", 11+i, 1, "s", "v6.3", "ctrl-v6.3", 0.90, 0.85, 1.0, 0.90, now, "click")
        for i in range(5)
    ]

    cert = gate.certify_policy_promotion("cand-v6.4", "ctrl-v6.3", cand_records, ctrl_records)
    assert cert.support_coverage == 0.40
    assert cert.is_approved is False
    reason_codes = [r["code"] for r in cert.decision["reasons"]]
    assert GovernanceRejectionCode.INSUFFICIENT_SUPPORT in reason_codes


def test_governance_certification_artifact_and_rejection_codes():
    """Verify PolicyAwareCertification payload structure, causal estimand metadata, and machine-readable rejection format."""
    gate = PolicyAwarePromotionGate(min_ess=1.0, min_ess_ratio=0.01, min_support_coverage=0.50)

    now = datetime.now(timezone.utc)
    cand_records = [
        ExposureRecord("e1", "r1", "u1", 11, 1, "s1", "v6.3", "cand-v6.4", 0.90, 0.85, 1.00, 0.90, now, "completion"),
        ExposureRecord("e2", "r2", "u2", 12, 2, "s2", "v6.3", "cand-v6.4", 0.90, 0.85, 0.707, 0.636, now, "like"),
        ExposureRecord("e3", "r3", "u3", 13, 1, "s3", "v6.3", "cand-v6.4", 0.90, 0.85, 1.00, 0.90, now, "watchlist")
    ]

    ctrl_records = [
        ExposureRecord("e10", "r1", "u1", 11, 1, "s1", "v6.3", "ctrl-v6.3", 0.90, 0.85, 1.00, 0.90, now, "click"),
        ExposureRecord("e20", "r2", "u2", 12, 2, "s2", "v6.3", "ctrl-v6.3", 0.90, 0.85, 0.707, 0.636, now, None),
        ExposureRecord("e30", "r3", "u3", 13, 1, "s3", "v6.3", "ctrl-v6.3", 0.90, 0.85, 1.00, 0.90, now, None)
    ]

    cert = gate.certify_policy_promotion(
        candidate_version="cand-v6.4",
        control_version="ctrl-v6.3",
        candidate_records=cand_records,
        control_records=ctrl_records,
        dataset_version="ds-2026-08",
        feature_snapshot_version="fs-2026-08"
    )

    assert cert.certification_id.startswith("cert-")
    assert cert.candidate_model_version == "cand-v6.4"
    assert cert.control_model_version == "ctrl-v6.3"
    assert cert.dataset_version == "ds-2026-08"
    assert cert.feature_snapshot_version == "fs-2026-08"
    assert cert.estimand == "policy_value"
    assert cert.outcome == "weighted_user_response"
    assert cert.observation_model == "selection_x_examination"
    assert cert.decision["status"] == "PROMOTE"
    assert cert.is_approved is True
    assert cert.candidate_snips > cert.control_snips

    cert_dict = cert.to_dict()
    assert cert_dict["governance_metadata"]["estimator_name"] == "clipped_importance_weighted_off_policy_estimator_with_controlled_variance"
