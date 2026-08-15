"""
Streamora Recommendation Platform — Deterministic Sticky Traffic Assignment Engine
Phase 7: Online Experimentation & Safe Model Deployment Platform

Implements SHA256 deterministic 10,000-bucket allocation, persistent sticky assignments
across progressive rollout stages, and experiment layer mutual exclusion.
"""

from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set

from services.recommendation.experiment_registry import (
    ExperimentLifecycleState,
    ExperimentRecord,
    ExperimentRegistry,
    StageThresholds,
)


@dataclass
class VariantAssignment:
    """Assignment decision payload for a user request."""
    user_id: str
    experiment_id: str
    experiment_layer: str
    variant: str  # "TREATMENT" | "CONTROL"
    model_version: str
    bucket: int
    stage: str
    is_sticky: bool = True
    assigned_at: datetime = field(default_factory=datetime.utcnow)


def compute_user_bucket(user_id: str, experiment_id: str) -> int:
    """Computes a deterministic hash bucket in range [0, 9999] using SHA256."""
    key = f"{user_id}:{experiment_id}".encode("utf-8")
    hash_hex = hashlib.sha256(key).hexdigest()
    return int(hash_hex[:8], 16) % 10000


class PersistentAssignmentStore:
    """In-memory persistent store for sticky user assignments across rollout stages."""

    def __init__(self):
        # (user_id, experiment_id) -> VariantAssignment
        self._assignments: Dict[Tuple[str, str], VariantAssignment] = {}
        # (user_id, experiment_layer) -> experiment_id
        self._layer_allocations: Dict[Tuple[str, str], str] = {}

    def get_assignment(self, user_id: str, experiment_id: str) -> Optional[VariantAssignment]:
        return self._assignments.get((user_id, experiment_id))

    def save_assignment(self, assignment: VariantAssignment):
        self._assignments[(assignment.user_id, assignment.experiment_id)] = assignment
        self._layer_allocations[(assignment.user_id, assignment.experiment_layer)] = assignment.experiment_id

    def get_active_layer_experiment(self, user_id: str, layer: str) -> Optional[str]:
        return self._layer_allocations.get((user_id, layer))


class ExperimentAssignmentEngine:
    """Engine responsible for resolving deterministic sticky user assignments."""

    def __init__(self, registry: ExperimentRegistry, store: Optional[PersistentAssignmentStore] = None):
        self.registry = registry
        self.store = store or PersistentAssignmentStore()

    def get_assignment(self, user_id: str, experiment_id: str) -> VariantAssignment:
        record = self.registry.get_experiment(experiment_id)
        if not record:
            raise KeyError(f"Experiment {experiment_id} not registered.")

        # Check existing sticky assignment
        existing = self.store.get_assignment(user_id, experiment_id)
        if existing:
            # If experiment rolled back, override sticky assignment to CONTROL
            if record.state in [ExperimentLifecycleState.ROLLED_BACK, ExperimentLifecycleState.TERMINATED]:
                return VariantAssignment(
                    user_id=user_id,
                    experiment_id=experiment_id,
                    experiment_layer=record.config.experiment_layer,
                    variant="CONTROL",
                    model_version=record.config.control_model_version,
                    bucket=existing.bucket,
                    stage=record.state.value,
                    is_sticky=True,
                )
            
            # If active stage threshold expanded, re-evaluate if previously CONTROL user is now eligible
            threshold = StageThresholds.get_threshold(record.state)
            if existing.bucket < threshold and existing.variant == "CONTROL":
                new_assignment = VariantAssignment(
                    user_id=user_id,
                    experiment_id=experiment_id,
                    experiment_layer=record.config.experiment_layer,
                    variant="TREATMENT",
                    model_version=record.config.candidate_model_version,
                    bucket=existing.bucket,
                    stage=record.state.value,
                    is_sticky=True,
                )
                self.store.save_assignment(new_assignment)
                return new_assignment
            return existing

        # Check layer mutual exclusion
        active_exp_in_layer = self.store.get_active_layer_experiment(user_id, record.config.experiment_layer)
        if active_exp_in_layer and active_exp_in_layer != experiment_id:
            # User already allocated to a different active experiment in this layer -> fallback to CONTROL
            bucket = compute_user_bucket(user_id, experiment_id)
            assignment = VariantAssignment(
                user_id=user_id,
                experiment_id=experiment_id,
                experiment_layer=record.config.experiment_layer,
                variant="CONTROL",
                model_version=record.config.control_model_version,
                bucket=bucket,
                stage=record.state.value,
                is_sticky=False,
            )
            return assignment

        # Compute new deterministic bucket
        bucket = compute_user_bucket(user_id, experiment_id)
        threshold = StageThresholds.get_threshold(record.state)

        # Check eligibility
        if record.state in [ExperimentLifecycleState.ROLLED_BACK, ExperimentLifecycleState.TERMINATED, ExperimentLifecycleState.DRAFT, ExperimentLifecycleState.READY]:
            variant = "CONTROL"
            model_version = record.config.control_model_version
        elif bucket < threshold:
            variant = "TREATMENT"
            model_version = record.config.candidate_model_version
        else:
            variant = "CONTROL"
            model_version = record.config.control_model_version

        assignment = VariantAssignment(
            user_id=user_id,
            experiment_id=experiment_id,
            experiment_layer=record.config.experiment_layer,
            variant=variant,
            model_version=model_version,
            bucket=bucket,
            stage=record.state.value,
            is_sticky=True,
        )
        self.store.save_assignment(assignment)
        return assignment
