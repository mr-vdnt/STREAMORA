"""
Phase 6.3 Policy-Aware Counterfactual Certification Master Test Suite.

Validates:
1. ExplorationPolicyModel: Non-zero exploration probability pi_0(a|x) > 0 under epsilon-greedy logging policy.
2. PolicyAwareExposureLogger: ExposureRecord contract with joint propensity computation.
3. CounterfactualEvaluator: Importance weight clipping (M), Effective Sample Size (ESS), and Delta-SNIPS 95% Bootstrap CIs.
4. PolicyAwarePromotionGate: Statistically rigorous candidate promotion/rejection gates.
"""
from datetime import datetime, timezone
import pytest
from services.recommendation.exposure_logger import PolicyAwareExposureLogger, ExplorationPolicyModel, PositionBiasModel, ExposureRecord
from services.recommendation.counterfactual_evaluator import CounterfactualEvaluator, PolicyAwarePromotionGate


def test_exploration_policy_model_support():
    """Verify non-zero exploration probability pi_0(a|x) under epsilon-greedy policy."""
    policy = ExplorationPolicyModel(epsilon=0.10)

    prob_primary = policy.get_logging_probability(is_primary_choice=True, candidate_pool_size=20)
    prob_explore = policy.get_logging_probability(is_primary_choice=False, candidate_pool_size=20)

    assert prob_primary > prob_explore > 0.0, "Logging probability pi_0(a|x) must be strictly non-zero for all candidate actions"
    assert prob_primary >= 0.90, "Primary choice probability should reflect 1-eps majority weight"


def test_policy_aware_exposure_record_contract():
    """Verify ExposureRecord contracts including joint propensity calculation."""
    logger = PolicyAwareExposureLogger(epsilon=0.10)

    rec = logger.log_policy_exposure(
        exposure_id="exp_63_01",
        request_id="req_63_01",
        user_id="user_test",
        item_id=101,
        rank=2,
        slate_id="slate_top_movies",
        logging_version="prod-v6.2",
        target_version="cand-v6.3",
        is_primary_choice=True,
        target_prob=0.85,
        pool_size=20
    )

    assert rec.exposure_id == "exp_63_01"
    assert rec.logging_probability > 0.0
    assert rec.examination_probability == PositionBiasModel.get_examination_probability(2)
    assert rec.joint_propensity == round(rec.logging_probability * rec.examination_probability, 5)
    assert rec.observed_response is None

    # Attach response
    logger.record_response("exp_63_01", 101, "completion")
    assert rec.observed_response == "completion"


def test_counterfactual_importance_weights_and_ess():
    """Verify importance weight clipping (M) and Effective Sample Size (ESS)."""
    evaluator = CounterfactualEvaluator(clip_max=10.0)
    now = datetime.now(timezone.utc)

    records = [
        ExposureRecord("e1", "r1", "u1", 11, 1, "s1", "v6.2", "v6.3", 0.905, 0.85, 1.00, 0.905, now, "completion"),
        ExposureRecord("e2", "r1", "u1", 12, 5, "s1", "v6.2", "v6.3", 0.005, 0.85, 0.447, 0.002, now, "like"),
        ExposureRecord("e3", "r2", "u2", 15, 10, "s2", "v6.2", "v6.3", 0.905, 0.85, 0.316, 0.286, now, None)
    ]

    w1 = evaluator.compute_importance_weight(records[0])
    w2 = evaluator.compute_importance_weight(records[1])  # Raw w = 0.85/0.002 = 425 -> clipped to 10.0
    ess = evaluator.compute_ess(records)

    assert w1 > 0.0
    assert w2 == 10.0, "Importance weight exceeding max bound must be clipped to M=10.0"
    assert ess > 0.0, "Effective Sample Size must be computed"


def test_policy_aware_promotion_gate_delta_snips_ci():
    """Verify promotion gate approves statistically superior candidate and rejects underperforming / low-ESS candidates."""
    gate = PolicyAwarePromotionGate(min_ess=1.2)
    now = datetime.now(timezone.utc)

    cand_records = [
        ExposureRecord("e1", "r1", "u1", 11, 1, "s1", "v6.2", "cand-v6.3", 0.90, 0.85, 1.00, 0.90, now, "completion"),
        ExposureRecord("e2", "r2", "u2", 12, 2, "s2", "v6.2", "cand-v6.3", 0.90, 0.85, 0.707, 0.636, now, "like"),
        ExposureRecord("e3", "r3", "u3", 13, 1, "s3", "v6.2", "cand-v6.3", 0.90, 0.85, 1.00, 0.90, now, "watchlist")
    ]

    ctrl_records = [
        ExposureRecord("e4", "r1", "u1", 15, 1, "s1", "v6.2", "ctrl-v6.2", 0.90, 0.85, 1.00, 0.90, now, "click"),
        ExposureRecord("e5", "r2", "u2", 16, 2, "s2", "v6.2", "ctrl-v6.2", 0.90, 0.85, 0.707, 0.636, now, None),
        ExposureRecord("e6", "r3", "u3", 17, 3, "s3", "v6.2", "ctrl-v6.2", 0.90, 0.85, 0.577, 0.519, now, None)
    ]

    # Superior Candidate -> Approved
    report_pass = gate.evaluate_for_promotion(
        candidate_version="cand-v6.3",
        control_version="ctrl-v6.2",
        candidate_records=cand_records,
        control_records=ctrl_records
    )

    assert report_pass.is_approved is True
    assert report_pass.delta_snips > 0.0
    assert report_pass.delta_ci_lower > 0.0

    # Underperforming Candidate -> Rejected
    report_fail = gate.evaluate_for_promotion(
        candidate_version="ctrl-v6.2",
        control_version="cand-v6.3",
        candidate_records=ctrl_records,
        control_records=cand_records
    )

    assert report_fail.is_approved is False
    assert len(report_fail.rejection_reasons) > 0
