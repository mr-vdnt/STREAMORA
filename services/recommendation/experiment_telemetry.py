"""
Streamora Recommendation Platform — Telemetry Collector & Metric Denominator Engine
Phase 7: Online Experimentation & Safe Model Deployment Platform

Implements exposure lineage tracking, outcome attribution, and explicit metric denominator calculations.
"""

from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Any


@dataclass
class ExposureLineageRecord:
    """Exposure Lineage Record binding assignment provenance to slate items."""
    exposure_id: str
    request_id: str
    experiment_id: str
    user_id: str
    variant: str  # "TREATMENT" | "CONTROL"
    model_version: str
    item_id: int
    rank: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserEventRecord:
    """Attributed downstream user interaction event."""
    event_id: str
    exposure_id: str
    request_id: str
    user_id: str
    event_type: str  # "click", "detail_view", "playback_start", "completion", "like", "dislike", "error"
    watch_time_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class VariantMetricSummary:
    """Explicitly computed online metric summary for a single variant."""
    variant: str
    exposures: int = 0
    unique_users: int = 0
    clicks: int = 0
    detail_views: int = 0
    playback_starts: int = 0
    completions: int = 0
    likes: int = 0
    dislikes: int = 0
    errors: int = 0
    recommendation_watch_time_seconds: float = 0.0
    exposed_items: Set[int] = field(default_factory=set)

    @property
    def ctr(self) -> float:
        return self.clicks / self.exposures if self.exposures > 0 else 0.0

    @property
    def detail_view_rate(self) -> float:
        return self.detail_views / self.exposures if self.exposures > 0 else 0.0

    @property
    def playback_start_rate(self) -> float:
        """Denominated by detail_views."""
        return self.playback_starts / self.detail_views if self.detail_views > 0 else 0.0

    @property
    def completion_rate(self) -> float:
        """Denominated by playback_starts."""
        return self.completions / self.playback_starts if self.playback_starts > 0 else 0.0

    @property
    def dislike_rate(self) -> float:
        return self.dislikes / self.exposures if self.exposures > 0 else 0.0

    @property
    def error_rate(self) -> float:
        return self.errors / self.exposures if self.exposures > 0 else 0.0

    def catalog_coverage(self, total_catalog_size: int = 100) -> float:
        if total_catalog_size <= 0:
            return 0.0
        return len(self.exposed_items) / float(total_catalog_size)

    def to_dict(self, total_catalog_size: int = 100) -> Dict[str, Any]:
        return {
            "variant": self.variant,
            "exposures": self.exposures,
            "unique_users": self.unique_users,
            "clicks": self.clicks,
            "detail_views": self.detail_views,
            "playback_starts": self.playback_starts,
            "completions": self.completions,
            "likes": self.likes,
            "dislikes": self.dislikes,
            "errors": self.errors,
            "ctr": round(self.ctr, 4),
            "detail_view_rate": round(self.detail_view_rate, 4),
            "playback_start_rate": round(self.playback_start_rate, 4),
            "completion_rate": round(self.completion_rate, 4),
            "dislike_rate": round(self.dislike_rate, 4),
            "error_rate": round(self.error_rate, 4),
            "catalog_coverage": round(self.catalog_coverage(total_catalog_size), 4),
            "recommendation_watch_time_seconds": round(self.recommendation_watch_time_seconds, 2),
        }


class ExperimentTelemetryCollector:
    """In-memory telemetry collector for online experiment evaluation."""

    def __init__(self, total_catalog_size: int = 100):
        self.total_catalog_size = total_catalog_size
        self._exposures: Dict[str, ExposureLineageRecord] = {}
        self._events: List[UserEventRecord] = []
        self._experiment_exposures: Dict[str, List[ExposureLineageRecord]] = {}

    def log_exposure(self, exposure: ExposureLineageRecord):
        self._exposures[exposure.exposure_id] = exposure
        if exposure.experiment_id not in self._experiment_exposures:
            self._experiment_exposures[exposure.experiment_id] = []
        self._experiment_exposures[exposure.experiment_id].append(exposure)

    def log_event(self, event: UserEventRecord):
        self._events.append(event)

    def get_summary(self, experiment_id: str) -> Dict[str, VariantMetricSummary]:
        exposures = self._experiment_exposures.get(experiment_id, [])
        treatment_summary = VariantMetricSummary(variant="TREATMENT")
        control_summary = VariantMetricSummary(variant="CONTROL")

        treatment_users: Set[str] = set()
        control_users: Set[str] = set()
        exposure_variant_map: Dict[str, str] = {}

        for exp in exposures:
            exposure_variant_map[exp.exposure_id] = exp.variant
            if exp.variant == "TREATMENT":
                treatment_summary.exposures += 1
                treatment_users.add(exp.user_id)
                treatment_summary.exposed_items.add(exp.item_id)
            else:
                control_summary.exposures += 1
                control_users.add(exp.user_id)
                control_summary.exposed_items.add(exp.item_id)

        treatment_summary.unique_users = len(treatment_users)
        control_summary.unique_users = len(control_users)

        for event in self._events:
            variant = exposure_variant_map.get(event.exposure_id)
            if not variant:
                continue

            summary = treatment_summary if variant == "TREATMENT" else control_summary
            etype = event.event_type.lower()
            if etype == "click":
                summary.clicks += 1
            elif etype == "detail_view":
                summary.detail_views += 1
            elif etype == "playback_start":
                summary.playback_starts += 1
            elif etype == "completion":
                summary.completions += 1
            elif etype == "like":
                summary.likes += 1
            elif etype == "dislike":
                summary.dislikes += 1
            elif etype == "error":
                summary.errors += 1

            if event.watch_time_seconds > 0:
                summary.recommendation_watch_time_seconds += event.watch_time_seconds

        return {
            "TREATMENT": treatment_summary,
            "CONTROL": control_summary
        }
