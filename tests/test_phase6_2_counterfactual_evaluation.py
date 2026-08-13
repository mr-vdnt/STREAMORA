"""
Phase 6.2 Counterfactual & Off-Policy Evaluation Master Certification Suite.

Validates:
1. PositionBiasPropensityModel: Decreasing observation propensity p(r) with rank position r.
2. ExposureLogger: Exposure provenance logging contracts.
3. CounterfactualEvaluator: Off-policy IPS & SNIPS calculation.
4. OffPolicyPromotionGate: Automated off-policy model promotion/rejection gates.
"""
from datetime import datetime, timezone
import pytest
from services.recommendation.exposure_logger import ExposureLogger, PositionBiasPropensityModel, ExposureLogEntry
from services.recommendation.counterfactual_evaluator import CounterfactualEvaluator, OffPolicyPromotionGate


def test_position_bias_propensity_model():
    """Verify observation propensity p(r) decreases with rank r."""
    prop_rank1 = PositionBiasPropensityModel.get_propensity(rank=1)
    prop_rank5 = PositionBiasPropensityModel.get_propensity(rank=5)
    prop_rank10 = PositionBiasPropensityModel.get_propensity(rank=10)

    assert prop_rank1 > prop_rank5 > prop_rank10, "Observation propensity must strictly decrease with lower rank positions"
    assert prop_rank1 == 1.0, "Rank 1 propensity should equal 1.0 baseline"


def test_exposure_logger_contracts():
    """Verify exposure provenance logging and response attachment contracts."""
    logger = ExposureLogger()

    entry = logger.log_exposure(
        exposure_id="exp_001",
        user_id="user_test",
        item_id=101,
        rank=2,
        model_version="candidate-v6.2"
    )

    assert entry.exposure_id == "exp_001"
    assert entry.user_id == "user_test"
    assert entry.item_id == 101
    assert entry.rank == 2
    assert entry.propensity_score < 1.0
    assert entry.observed_response is None

    # Attach user response
    logger.record_response("exp_001", 101, "completion")
    assert entry.observed_response == "completion"


def test_counterfactual_ips_and_snips_calculation():
    """Verify IPS and SNIPS off-policy calculations."""
    evaluator = CounterfactualEvaluator()
    now = datetime.now(timezone.utc)

    logs = [
        ExposureLogEntry("exp1", "u1", 11, 1, 1.0000, "v6.2", now, "completion"),  # reward=1.0, p=1.0000 -> y/p = 1.0
        ExposureLogEntry("exp2", "u1", 12, 5, 0.4472, "v6.2", now, "like"),        # reward=1.0, p=0.4472 -> y/p = 2.236
        ExposureLogEntry("exp3", "u2", 15, 10, 0.3162, "v6.2", now, None)           # reward=0.0, p=0.3162 -> y/p = 0.0
    ]

    ips = evaluator.compute_ips(logs)
    snips = evaluator.compute_snips(logs)

    assert ips > 0.0
    assert snips > 0.0
    assert 0.0 <= snips <= 1.0, "SNIPS score must be bounded in [0, 1]"


def test_off_policy_promotion_decision_gate():
    """Verify off-policy promotion gate approves superior candidate and rejects inferior candidate."""
    gate = OffPolicyPromotionGate()
    now = datetime.now(timezone.utc)

    # Candidate logs: high completion rate at rank 5 (high IPS reward)
    cand_logs = [
        ExposureLogEntry("e1", "u1", 11, 1, 1.0000, "cand-v6.2", now, "completion"),
        ExposureLogEntry("e2", "u2", 12, 5, 0.4472, "cand-v6.2", now, "like")
    ]

    # Control logs: lower rewards
    ctrl_logs = [
        ExposureLogEntry("e3", "u1", 15, 1, 1.0000, "ctrl-v6.1", now, "click"),
        ExposureLogEntry("e4", "u2", 16, 2, 0.7071, "ctrl-v6.1", now, None)
    ]

    report_pass = gate.evaluate_for_promotion(
        candidate_version="cand-v6.2",
        control_version="ctrl-v6.1",
        candidate_logs=cand_logs,
        control_logs=ctrl_logs
    )

    assert report_pass.is_approved is True
    assert len(report_pass.rejection_reasons) == 0

    # Underperforming candidate -> Rejection
    report_fail = gate.evaluate_for_promotion(
        candidate_version="ctrl-v6.1",
        control_version="cand-v6.2",
        candidate_logs=ctrl_logs,
        control_logs=cand_logs
    )

    assert report_fail.is_approved is False
    assert len(report_fail.rejection_reasons) > 0
