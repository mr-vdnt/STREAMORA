"""
Model Registry & Version Lifecycle Manager for Streamora Phase 6.

Provides versioned model registry, metadata storage, offline metric benchmarks,
shadow deployment hooks, and 1-step instant rollback.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any


@dataclass
class ModelArtifact:
    version: str
    model_name: str
    created_at: datetime
    weights: Dict[str, float]
    feature_importance: Dict[str, float]
    offline_metrics: Dict[str, float]
    is_active: bool = False
    is_shadow: bool = False


class ModelRegistry:
    """Versioned artifact repository with instant rollback capabilities."""

    def __init__(self):
        self._artifacts: Dict[str, ModelArtifact] = {}
        self._active_version: Optional[str] = None
        self._shadow_version: Optional[str] = None

    def register_model(self, artifact: ModelArtifact) -> None:
        self._artifacts[artifact.version] = artifact
        if artifact.is_active or self._active_version is None:
            self.promote_model(artifact.version)

    def promote_model(self, version: str) -> None:
        if version not in self._artifacts:
            raise ValueError(f"Model version '{version}' not found in registry")

        for v, art in self._artifacts.items():
            art.is_active = (v == version)
        self._active_version = version

    def set_shadow_model(self, version: str) -> None:
        if version not in self._artifacts:
            raise ValueError(f"Shadow model version '{version}' not found")

        for v, art in self._artifacts.items():
            art.is_shadow = (v == version)
        self._shadow_version = version

    def rollback_model(self, target_version: str) -> None:
        """One-step return to previous model artifact."""
        self.promote_model(target_version)

    def get_active_model(self) -> Optional[ModelArtifact]:
        if self._active_version:
            return self._artifacts.get(self._active_version)
        return None

    def get_shadow_model(self) -> Optional[ModelArtifact]:
        if self._shadow_version:
            return self._artifacts.get(self._shadow_version)
        return None
