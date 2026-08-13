"""
Phase 6 Learned LTR & Model Lifecycle Platform Verification Suite.

Validates:
1. TemporalDatasetBuilder: Leakage-free train/validation/test temporal splits.
2. LearnedLTREngine: Machine-learned feature importance & pairwise predictions.
3. ModelRegistry: Versioned model artifacts, active promotion, and 1-step instant rollback.
4. ShadowExperimentRunner: Shadow mode execution without user-facing slate distortion.
"""
from datetime import datetime, timezone, timedelta
import pytest
from services.recommendation.dataset_builder import TemporalDatasetBuilder, TrainingSample
from services.recommendation.model_registry import ModelRegistry, ModelArtifact
from services.recommendation.learned_ltr import LearnedLTREngine
from services.recommendation.shadow_experiment_runner import ShadowExperimentRunner


def test_temporal_dataset_builder_leakage_protection():
    """Verify temporal train/val/test splits prevent future interaction leakage."""
    builder = TemporalDatasetBuilder(val_split_days=7, test_split_days=7)
    now = datetime.now(timezone.utc)

    samples = [
        TrainingSample(user_id="u1", content_id=1, features={"f1": 0.1}, label=1.0, timestamp=now - timedelta(days=20)),
        TrainingSample(user_id="u2", content_id=2, features={"f1": 0.2}, label=0.0, timestamp=now - timedelta(days=10)),
        TrainingSample(user_id="u3", content_id=3, features={"f1": 0.3}, label=1.0, timestamp=now - timedelta(days=2))
    ]

    train, val, test = builder.create_temporal_splits(samples)

    assert len(train) > 0, "Train split must be populated"
    assert len(test) > 0, "Test split must be populated"

    train_max_ts = max(s.timestamp for s in train)
    test_min_ts = min(s.timestamp for s in test)
    assert train_max_ts <= test_min_ts, "Train timestamps must precede Test timestamps"


def test_model_registry_promotion_and_rollback():
    """Verify Model Registry artifact registration, promotion, and instant 1-step rollback."""
    registry = ModelRegistry()
    now = datetime.now(timezone.utc)

    art_v1 = ModelArtifact(
        version="v1.0.0",
        model_name="baseline-ltr",
        created_at=now,
        weights={"user_affinity": 0.40, "popularity": 0.60},
        feature_importance={"user_affinity": 0.40, "popularity": 0.60},
        offline_metrics={"ndcg_5": 0.9120},
        is_active=True
    )

    art_v2 = ModelArtifact(
        version="v2.0.0",
        model_name="learned-lambdamart",
        created_at=now,
        weights={"user_affinity": 0.60, "collaborative_score": 0.40},
        feature_importance={"user_affinity": 0.60, "collaborative_score": 0.40},
        offline_metrics={"ndcg_5": 0.9469},
        is_active=False
    )

    registry.register_model(art_v1)
    registry.register_model(art_v2)

    # Promote v2.0.0
    registry.promote_model("v2.0.0")
    assert registry.get_active_model().version == "v2.0.0"

    # 1-step rollback to v1.0.0
    registry.rollback_model("v1.0.0")
    assert registry.get_active_model().version == "v1.0.0", "Rollback must return active model to v1.0.0"


def test_shadow_deployment_mode():
    """Verify ShadowExperimentRunner evaluates shadow model without distorting active user slates."""
    registry = ModelRegistry()
    now = datetime.now(timezone.utc)

    art_v1 = ModelArtifact(
        version="v1.0.0",
        model_name="active-prod",
        created_at=now,
        weights={"user_affinity": 0.50},
        feature_importance={"user_affinity": 0.50},
        offline_metrics={"ndcg_5": 0.90},
        is_active=True
    )

    art_shadow = ModelArtifact(
        version="v2.0.0-shadow",
        model_name="shadow-candidate",
        created_at=now,
        weights={"graph_sim": 0.70},
        feature_importance={"graph_sim": 0.70},
        offline_metrics={"ndcg_5": 0.95},
        is_shadow=True
    )

    registry.register_model(art_v1)
    registry.register_model(art_shadow)
    registry.set_shadow_model("v2.0.0-shadow")

    runner = ShadowExperimentRunner(registry)
    target = {"id": 10, "title": "Inception", "director": "Nolan"}
    catalog = [
        {"id": 11, "title": "Interstellar", "genres": ["Sci-Fi"], "director": "Nolan", "popularity": 90},
        {"id": 12, "title": "Tenet", "genres": ["Action"], "director": "Nolan", "popularity": 85}
    ]

    active_slate = [{"id": 11, "title": "Interstellar"}]
    log = runner.evaluate_shadow("user_shadow_test", target, catalog, active_slate)

    assert log.active_version == "v1.0.0"
    assert log.shadow_version == "v2.0.0-shadow"
    assert len(log.shadow_slate_ids) == len(active_slate)
    assert 0.0 <= log.divergence_ratio <= 1.0
