"""
Streamora Recommendation Platform — Experiment Registry & Lifecycle State Machine
Phase 7: Online Experimentation & Safe Model Deployment Platform

Defines experiment configuration schemas, state machine enums, namespace layers,
and persistent versioned experiment records with optimistic concurrency control.
"""

from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


class ExperimentLifecycleState(Enum):
    """Production Experiment Lifecycle State Machine."""
    DRAFT = "DRAFT"
    READY = "READY"
    SHADOW = "SHADOW"
    STAGE_5PCT = "STAGE_5PCT"
    STAGE_10PCT = "STAGE_10PCT"
    STAGE_25PCT = "STAGE_25PCT"
    STAGE_50PCT = "STAGE_50PCT"
    PROMOTED_100PCT = "PROMOTED_100PCT"
    ROLLED_BACK = "ROLLED_BACK"
    TERMINATED = "TERMINATED"

    @classmethod
    def active_stages(cls) -> List[ExperimentLifecycleState]:
        return [
            cls.SHADOW,
            cls.STAGE_5PCT,
            cls.STAGE_10PCT,
            cls.STAGE_25PCT,
            cls.STAGE_50PCT,
            cls.PROMOTED_100PCT,
        ]


class ExperimentLayer(Enum):
    """Namespace layers to enforce mutual exclusion across overlapping experiments."""
    RECOMMENDATION_RANKER = "RECOMMENDATION_RANKER"
    CANDIDATE_GENERATOR = "CANDIDATE_GENERATOR"
    DIVERSIFICATION_MMR = "DIVERSIFICATION_MMR"
    HOME_SHELF_LAYOUT = "HOME_SHELF_LAYOUT"


@dataclass
class StageThresholds:
    """Traffic bucket upper bounds out of 10,000."""
    SHADOW: int = 0
    STAGE_5PCT: int = 500
    STAGE_10PCT: int = 1000
    STAGE_25PCT: int = 2500
    STAGE_50PCT: int = 5000
    PROMOTED_100PCT: int = 10000

    @classmethod
    def get_threshold(cls, state: ExperimentLifecycleState) -> int:
        mapping = {
            ExperimentLifecycleState.SHADOW: cls.SHADOW,
            ExperimentLifecycleState.STAGE_5PCT: cls.STAGE_5PCT,
            ExperimentLifecycleState.STAGE_10PCT: cls.STAGE_10PCT,
            ExperimentLifecycleState.STAGE_25PCT: cls.STAGE_25PCT,
            ExperimentLifecycleState.STAGE_50PCT: cls.STAGE_50PCT,
            ExperimentLifecycleState.PROMOTED_100PCT: cls.PROMOTED_100PCT,
        }
        return mapping.get(state, 0)


@dataclass
class ExperimentConfig:
    """Immutable Configuration Payload for an Online Experiment."""
    experiment_id: str
    experiment_layer: str
    control_model_version: str
    candidate_model_version: str
    phase6_4_certification_id: str
    dataset_version: str
    feature_snapshot_version: str
    owner: str = "recommendation_mlops"
    created_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1


@dataclass
class ExperimentRecord:
    """Persistent state record for an experiment with optimistic concurrency control."""
    config: ExperimentConfig
    state: ExperimentLifecycleState = ExperimentLifecycleState.DRAFT
    version: int = 1
    updated_at: datetime = field(default_factory=datetime.utcnow)
    state_history: List[Dict[str, Any]] = field(default_factory=list)
    rollback_reason: Optional[str] = None

    def record_transition(self, new_state: ExperimentLifecycleState, actor: str = "rollout_controller", reason: str = ""):
        self.state_history.append({
            "from_state": self.state.value,
            "to_state": new_state.value,
            "version_before": self.version,
            "version_after": self.version + 1,
            "actor": actor,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.state = new_state
        self.version += 1
        self.updated_at = datetime.utcnow()
        if new_state == ExperimentLifecycleState.ROLLED_BACK:
            self.rollback_reason = reason


class ExperimentRegistry:
    """In-memory persistent registry for production online experiments."""

    def __init__(self):
        self._experiments: Dict[str, ExperimentRecord] = {}

    def register_experiment(self, config: ExperimentConfig) -> ExperimentRecord:
        if not config.phase6_4_certification_id:
            raise ValueError(f"Experiment {config.experiment_id} rejected: missing Phase 6.4 certification_id prerequisite.")
        record = ExperimentRecord(config=config, state=ExperimentLifecycleState.READY)
        record.record_transition(ExperimentLifecycleState.READY, reason="Registered with Phase 6.4 prerequisite certification")
        self._experiments[config.experiment_id] = record
        return record

    def get_experiment(self, experiment_id: str) -> Optional[ExperimentRecord]:
        return self._experiments.get(experiment_id)

    def list_experiments(self) -> List[ExperimentRecord]:
        return list(self._experiments.values())

    def update_state_atomic(
        self,
        experiment_id: str,
        expected_version: int,
        new_state: ExperimentLifecycleState,
        reason: str = ""
    ) -> ExperimentRecord:
        record = self._experiments.get(experiment_id)
        if not record:
            raise KeyError(f"Experiment {experiment_id} not found.")
        if record.version != expected_version:
            raise RuntimeError(
                f"Optimistic concurrency failure for experiment {experiment_id}: "
                f"expected version {expected_version}, actual version {record.version}."
            )
        
        # Enforce state machine rules
        if record.state == ExperimentLifecycleState.TERMINATED:
            raise ValueError(f"Cannot update state for terminated experiment {experiment_id}.")
        if record.state == ExperimentLifecycleState.ROLLED_BACK and new_state != ExperimentLifecycleState.TERMINATED:
            raise ValueError(f"Rolled back experiment {experiment_id} can only transition to TERMINATED.")
        
        record.record_transition(new_state, reason=reason)
        return record
