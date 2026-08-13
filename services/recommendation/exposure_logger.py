"""
Exposure Provenance Logger & Position Bias Propensity Model for Streamora Phase 6.2.

Explicitly separates EXPOSURE (rank/position observation) from PREFERENCE (completion/like).
Calculates inverse propensity scores p(r) to correct position bias during counterfactual off-policy evaluation.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import math


@dataclass
class ExposureLogEntry:
    exposure_id: str
    user_id: str
    item_id: int
    rank: int
    propensity_score: float
    model_version: str
    timestamp: datetime
    observed_response: Optional[str] = None  # "click", "completion", "like", None


class PositionBiasPropensityModel:
    """Calculates observation propensity p(r) as a function of item rank r."""

    @staticmethod
    def get_propensity(rank: int, eta: float = 0.50) -> float:
        """Calculates propensity p(r) = 1 / (r ^ eta). Ensures p(r) > 0."""
        r = max(1, rank)
        propensity = 1.0 / (r ** eta)
        return max(0.05, round(propensity, 4))


class ExposureLogger:
    """Logs recommendation exposures with rank position propensity scores."""

    def __init__(self):
        self._logs: List[ExposureLogEntry] = []
        self.propensity_model = PositionBiasPropensityModel()

    def log_exposure(
        self, exposure_id: str, user_id: str, item_id: int, rank: int, model_version: str
    ) -> ExposureLogEntry:
        propensity = self.propensity_model.get_propensity(rank)
        entry = ExposureLogEntry(
            exposure_id=exposure_id,
            user_id=user_id,
            item_id=item_id,
            rank=rank,
            propensity_score=propensity,
            model_version=model_version,
            timestamp=datetime.now(timezone.utc)
        )
        self._logs.append(entry)
        return entry

    def record_response(self, exposure_id: str, item_id: int, response_type: str) -> None:
        for log in self._logs:
            if log.exposure_id == exposure_id and log.item_id == item_id:
                log.observed_response = response_type
                break

    def get_logs(self) -> List[ExposureLogEntry]:
        return self._logs
