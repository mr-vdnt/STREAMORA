"""
Streamora Master Test Suite — Phase 7: Online Experimentation & Safe Model Deployment Platform

Verifies:
1. SHA256 sticky user assignment across progressive rollout stages.
2. Sample-size reliability gates preventing spurious rollbacks on small sample sizes.
3. Absolute vs relative guardrail delta calculations across 5 health guardrails.
4. Multi-stage progressive deployment state machine & optimistic concurrency protection.
5. Automated emergency rollback on guardrail breach & creation of immutable OnlineExperimentReport artifacts.
"""

import pytest
import uuid
from datetime import datetime
from services.recommendation.experiment_registry import (
    ExperimentConfig,
    ExperimentLifecycleState,
    ExperimentRecord,
    ExperimentRegistry,
    ExperimentLayer,
    StageThresholds,
)
from services.recommendation.experiment_assignment import (
    ExperimentAssignmentEngine,
    PersistentAssignmentStore,
    compute_user_bucket,
)
from services.recommendation.experiment_telemetry import (
    ExperimentTelemetryCollector,
    ExposureLineageRecord,
    UserEventRecord,
)
from services.recommendation.guardrail_engine import (
    GuardrailEngine,
    GuardrailThresholds,
)
from services.recommendation.rollout_controller import ProgressiveRolloutController
from services.recommendation.experiment_report import ExperimentGovernanceReporter


def test_sticky_user_assignment_across_rollout_stages():
    """Certifies deterministic SHA256 bucket allocation and sticky user assignment."""
    registry = ExperimentRegistry()
    config = ExperimentConfig(
        experiment_id="exp_ltr_v8_001",
        experiment_layer=ExperimentLayer.RECOMMENDATION_RANKER.value,
        control_model_version="ltr_v7.2.0",
        candidate_model_version="ltr_v8.0.0_candidate",
        phase6_4_certification_id="cert_p64_9921_pass",
        dataset_version="ds_2026_w32",
        feature_snapshot_version="fs_v4.1",
    )
    record = registry.register_experiment(config)
    store = PersistentAssignmentStore()
    engine = ExperimentAssignmentEngine(registry=registry, store=store)

    user_id = "user_test_4892"
    bucket = compute_user_bucket(user_id, "exp_ltr_v8_001")
    assert 0 <= bucket <= 9999

    # Initially READY -> Control
    a0 = engine.get_assignment(user_id, "exp_ltr_v8_001")
    assert a0.variant == "CONTROL"

    # Advance to STAGE_5PCT
    registry.update_state_atomic("exp_ltr_v8_001", record.version, ExperimentLifecycleState.STAGE_5PCT)

    # Force a bucket < 500 for testing treatment
    user_treatment = "user_treatment_bucket_low"
    # Find a user string with bucket < 500
    for idx in range(1000):
        test_u = f"user_low_{idx}"
        if compute_user_bucket(test_u, "exp_ltr_v8_001") < 500:
            user_treatment = test_u
            break

    a1 = engine.get_assignment(user_treatment, "exp_ltr_v8_001")
    assert a1.variant == "TREATMENT"

    # Advance stage to 10%, 25%, 50%, 100% -> user remains sticky in TREATMENT
    for stage in [
        ExperimentLifecycleState.STAGE_10PCT,
        ExperimentLifecycleState.STAGE_25PCT,
        ExperimentLifecycleState.STAGE_50PCT,
        ExperimentLifecycleState.PROMOTED_100PCT,
    ]:
        rec = registry.get_experiment("exp_ltr_v8_001")
        registry.update_state_atomic("exp_ltr_v8_001", rec.version, stage)
        a_stage = engine.get_assignment(user_treatment, "exp_ltr_v8_001")
        assert a_stage.variant == "TREATMENT"
        assert a_stage.is_sticky is True


def test_sample_size_reliability_gate():
    """Certifies that small sample sizes return INSUFFICIENT_SAMPLE and hold stage."""
    registry = ExperimentRegistry()
    config = ExperimentConfig(
        experiment_id="exp_small_sample_002",
        experiment_layer=ExperimentLayer.RECOMMENDATION_RANKER.value,
        control_model_version="ltr_v7.2.0",
        candidate_model_version="ltr_v8.0.0_cand",
        phase6_4_certification_id="cert_p64_002",
        dataset_version="ds_v1",
        feature_snapshot_version="fs_v1",
    )
    record = registry.register_experiment(config)
    registry.update_state_atomic("exp_small_sample_002", record.version, ExperimentLifecycleState.STAGE_5PCT)

    telemetry = ExperimentTelemetryCollector()
    # Log only 5 exposures (< 30 min required)
    for i in range(5):
        telemetry.log_exposure(ExposureLineageRecord(
            exposure_id=f"exp_{i}",
            request_id=f"req_{i}",
            experiment_id="exp_small_sample_002",
            user_id=f"u_{i}",
            variant="TREATMENT" if i % 2 == 0 else "CONTROL",
            model_version="v8" if i % 2 == 0 else "v7",
            item_id=101 + i,
            rank=1
        ))

    controller = ProgressiveRolloutController(registry=registry, telemetry=telemetry)
    decision = controller.evaluate_and_step("exp_small_sample_002")

    assert decision.decision == "HOLD"
    assert decision.guardrail_report.status_code == "INSUFFICIENT_SAMPLE"
    assert decision.current_stage == "STAGE_5PCT"


def test_absolute_and_relative_guardrail_evaluations():
    """Certifies absolute and relative delta computations across 5 health guardrails."""
    guardrail = GuardrailEngine(thresholds=GuardrailThresholds(
        min_treatment_exposures=10,
        min_control_exposures=10,
        min_outcomes=5,
        max_completion_relative_drop=0.05,
        max_absolute_error_rate=0.01,
        max_latency_p95_relative_increase=0.20,
        min_absolute_catalog_coverage=0.50,
        max_absolute_dislike_rate=0.10,
    ))

    telemetry = ExperimentTelemetryCollector(total_catalog_size=10)

    # 50 exposures for Control & Treatment
    for i in range(50):
        # Treatment exposures
        telemetry.log_exposure(ExposureLineageRecord(
            exposure_id=f"trt_exp_{i}",
            request_id=f"req_t_{i}",
            experiment_id="exp_guardrail_test",
            user_id=f"u_t_{i}",
            variant="TREATMENT",
            model_version="cand_v1",
            item_id=(i % 8) + 1,
            rank=1
        ))
        # Control exposures
        telemetry.log_exposure(ExposureLineageRecord(
            exposure_id=f"ctrl_exp_{i}",
            request_id=f"req_c_{i}",
            experiment_id="exp_guardrail_test",
            user_id=f"u_c_{i}",
            variant="CONTROL",
            model_version="ctrl_v1",
            item_id=(i % 8) + 1,
            rank=1
        ))

        # Log healthy outcomes
        telemetry.log_event(UserEventRecord(
            event_id=f"e_t_{i}",
            exposure_id=f"trt_exp_{i}",
            request_id=f"req_t_{i}",
            user_id=f"u_t_{i}",
            event_type="detail_view"
        ))
        telemetry.log_event(UserEventRecord(
            event_id=f"e_c_{i}",
            exposure_id=f"ctrl_exp_{i}",
            request_id=f"req_c_{i}",
            user_id=f"u_c_{i}",
            event_type="detail_view"
        ))

        telemetry.log_event(UserEventRecord(
            event_id=f"p_t_{i}",
            exposure_id=f"trt_exp_{i}",
            request_id=f"req_t_{i}",
            user_id=f"u_t_{i}",
            event_type="playback_start"
        ))
        telemetry.log_event(UserEventRecord(
            event_id=f"p_c_{i}",
            exposure_id=f"ctrl_exp_{i}",
            request_id=f"req_c_{i}",
            user_id=f"u_c_{i}",
            event_type="playback_start"
        ))

        telemetry.log_event(UserEventRecord(
            event_id=f"c_t_{i}",
            exposure_id=f"trt_exp_{i}",
            request_id=f"req_t_{i}",
            user_id=f"u_t_{i}",
            event_type="completion",
            watch_time_seconds=120.0
        ))
        telemetry.log_event(UserEventRecord(
            event_id=f"c_c_{i}",
            exposure_id=f"ctrl_exp_{i}",
            request_id=f"req_c_{i}",
            user_id=f"u_c_{i}",
            event_type="completion",
            watch_time_seconds=120.0
        ))

    summary = telemetry.get_summary("exp_guardrail_test")
    report = guardrail.evaluate(
        treatment=summary["TREATMENT"],
        control=summary["CONTROL"],
        treatment_p95_latency_ms=4.0,
        control_p95_latency_ms=3.8,
        total_catalog_size=10
    )

    assert report.overall_passed is True
    assert report.status_code == "PASSED"
    assert len(report.checks) == 5


def test_progressive_multi_stage_rollout_and_concurrency():
    """Certifies multi-stage state machine transitions and optimistic concurrency failure handling."""
    registry = ExperimentRegistry()
    config = ExperimentConfig(
        experiment_id="exp_stage_flow_003",
        experiment_layer=ExperimentLayer.RECOMMENDATION_RANKER.value,
        control_model_version="ctrl_v1",
        candidate_model_version="cand_v1",
        phase6_4_certification_id="cert_p64_flow",
        dataset_version="ds_v1",
        feature_snapshot_version="fs_v1",
    )
    record = registry.register_experiment(config)
    assert record.state == ExperimentLifecycleState.READY

    # Test Optimistic Concurrency Failure: Attempt update with wrong version
    with pytest.raises(RuntimeError, match="Optimistic concurrency failure"):
        registry.update_state_atomic("exp_stage_flow_003", expected_version=99, new_state=ExperimentLifecycleState.SHADOW)

    # Valid step 1: READY -> SHADOW
    rec1 = registry.update_state_atomic("exp_stage_flow_003", expected_version=record.version, new_state=ExperimentLifecycleState.SHADOW)
    assert rec1.state == ExperimentLifecycleState.SHADOW

    # Valid step 2: SHADOW -> STAGE_5PCT
    rec2 = registry.update_state_atomic("exp_stage_flow_003", expected_version=rec1.version, new_state=ExperimentLifecycleState.STAGE_5PCT)
    assert rec2.state == ExperimentLifecycleState.STAGE_5PCT


def test_automated_emergency_rollback_and_governance_report():
    """Certifies emergency rollback on guardrail breach and creation of immutable OnlineExperimentReport."""
    registry = ExperimentRegistry()
    config = ExperimentConfig(
        experiment_id="exp_rollback_test_004",
        experiment_layer=ExperimentLayer.RECOMMENDATION_RANKER.value,
        control_model_version="ltr_v7.2.0",
        candidate_model_version="ltr_v8.0.0_flawed",
        phase6_4_certification_id="cert_p64_rollback_test",
        dataset_version="ds_2026_w32",
        feature_snapshot_version="fs_v4.1",
    )
    record = registry.register_experiment(config)
    registry.update_state_atomic("exp_rollback_test_004", record.version, ExperimentLifecycleState.STAGE_10PCT)

    telemetry = ExperimentTelemetryCollector(total_catalog_size=10)

    # Populate telemetry with 50 exposures for Control & Treatment
    for i in range(50):
        telemetry.log_exposure(ExposureLineageRecord(
            exposure_id=f"trt_exp_{i}",
            request_id=f"req_t_{i}",
            experiment_id="exp_rollback_test_004",
            user_id=f"u_t_{i}",
            variant="TREATMENT",
            model_version="flawed_v8",
            item_id=1,
            rank=1
        ))
        telemetry.log_exposure(ExposureLineageRecord(
            exposure_id=f"ctrl_exp_{i}",
            request_id=f"req_c_{i}",
            experiment_id="exp_rollback_test_004",
            user_id=f"u_c_{i}",
            variant="CONTROL",
            model_version="ctrl_v7",
            item_id=(i % 8) + 1,
            rank=1
        ))

        # Log outcome events
        telemetry.log_event(UserEventRecord(
            event_id=f"ev_c_{i}",
            exposure_id=f"ctrl_exp_{i}",
            request_id=f"req_c_{i}",
            user_id=f"u_c_{i}",
            event_type="detail_view"
        ))
        telemetry.log_event(UserEventRecord(
            event_id=f"ev_t_{i}",
            exposure_id=f"trt_exp_{i}",
            request_id=f"req_t_{i}",
            user_id=f"u_t_{i}",
            event_type="detail_view"
        ))

        # Intentionally inject high error rate into Treatment (5 errors out of 50 = 10% > 1% max allowed)
        if i < 5:
            telemetry.log_event(UserEventRecord(
                event_id=f"ev_err_{i}",
                exposure_id=f"trt_exp_{i}",
                request_id=f"req_t_{i}",
                user_id=f"u_t_{i}",
                event_type="error"
            ))

    controller = ProgressiveRolloutController(registry=registry, telemetry=telemetry)
    decision = controller.evaluate_and_step("exp_rollback_test_004")

    # Assert Emergency Rollback Triggered
    assert decision.decision == "ROLLBACK"
    assert decision.current_stage == "ROLLED_BACK"
    assert "error_rate_spike" in decision.guardrail_report.breached_guardrails

    rec_updated = registry.get_experiment("exp_rollback_test_004")
    assert rec_updated.state == ExperimentLifecycleState.ROLLED_BACK
    assert rec_updated.rollback_reason is not None

    # Generate immutable governance report
    summaries = telemetry.get_summary("exp_rollback_test_004")
    report = ExperimentGovernanceReporter.generate_report(
        record=rec_updated,
        treatment_summary=summaries["TREATMENT"],
        control_summary=summaries["CONTROL"],
        last_decision=decision,
        total_catalog_size=10
    )

    report_dict = report.to_dict()
    assert report_dict["final_state"] == "ROLLED_BACK"
    assert report_dict["final_decision"] == "ROLLBACK"
    assert report_dict["phase6_4_certification_id"] == "cert_p64_rollback_test"
    assert len(report_dict["certification_hash"]) == 64
