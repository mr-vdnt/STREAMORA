"""
Policy-Aware Exposure Provenance & Exploration Logger for Streamora Phase 6.3.

Records explicit joint propensity scores combining logging policy probability pi_0(a|x)
and position examination probability P(examined|rank), with epsilon-exploration support.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import math
import random


@dataclass
class ExposureRecord:
    exposure_id: str
    request_id: str
    user_id: str
    item_id: int
    rank: int
    slate_id: str = "slate_default"
    logging_policy_version: str = "prod-v6.2"
    target_policy_version: str = "v6.3"
    logging_probability: float = 0.90      # pi_0(a|x)
    target_probability: float = 0.85       # pi_1(a|x)
    examination_probability: float = 1.0  # P(examined|rank)
    joint_propensity: float = 0.90         # pi_0(a|x) * P(examined|rank)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    observed_response: Optional[str] = None  # "click", "completion", "like", None

    def __post_init__(self):
        # Type safety validation in case positional args mismatch
        if not isinstance(self.logging_probability, (int, float)):
            self.logging_probability = 0.90
        if not isinstance(self.examination_probability, (int, float)):
            self.examination_probability = 1.0
        self.joint_propensity = max(0.001, round(self.logging_probability * self.examination_probability, 5))

    # Backward compatibility properties
    @property
    def propensity_score(self) -> float:
        return self.examination_probability

    @property
    def model_version(self) -> str:
        return self.target_policy_version


class ExplorationPolicyModel:
    """Epsilon-greedy exploration policy model providing non-zero pi_0(a|x) support."""

    def __init__(self, epsilon: float = 0.10):
        self.epsilon = epsilon

    def get_logging_probability(self, is_primary_choice: bool, candidate_pool_size: int = 20) -> float:
        k = max(1, candidate_pool_size)
        if is_primary_choice:
            prob = (1.0 - self.epsilon) + (self.epsilon / float(k))
        else:
            prob = self.epsilon / float(k)
        return max(0.01, round(prob, 4))


class PositionBiasModel:
    """Calculates examination probability P(examined|rank)."""

    @staticmethod
    def get_examination_probability(rank: int, eta: float = 0.50) -> float:
        r = max(1, rank)
        prob = 1.0 / (r ** eta)
        return max(0.05, round(prob, 4))

    @staticmethod
    def get_propensity(rank: int, eta: float = 0.50) -> float:
        return PositionBiasModel.get_examination_probability(rank, eta)


# Alias for backward compatibility
PositionBiasPropensityModel = PositionBiasModel


def ExposureLogEntry(
    exposure_id: str,
    user_id: str,
    item_id: int,
    rank: int,
    propensity_score: float = 1.0,
    model_version: str = "v6.2",
    timestamp: Optional[datetime] = None,
    observed_response: Optional[str] = None
) -> ExposureRecord:
    """Factory helper for Phase 6.2 backward compatibility."""
    ts = timestamp or datetime.now(timezone.utc)
    return ExposureRecord(
        exposure_id=exposure_id,
        request_id="req_compat",
        user_id=user_id,
        item_id=item_id,
        rank=rank,
        slate_id="slate_compat",
        logging_policy_version="compat-v6.2",
        target_policy_version=model_version,
        logging_probability=0.90,
        target_probability=0.85,
        examination_probability=propensity_score,
        joint_propensity=round(0.90 * propensity_score, 5),
        timestamp=ts,
        observed_response=observed_response
    )


class PolicyAwareExposureLogger:
    """Logs recommendation exposures with explicit policy probabilities and joint propensities."""

    def __init__(self, epsilon: float = 0.10):
        self._records: List[ExposureRecord] = []
        self.exploration_model = ExplorationPolicyModel(epsilon=epsilon)
        self.position_model = PositionBiasModel()

    def log_policy_exposure(
        self,
        exposure_id: str,
        request_id: str,
        user_id: str,
        item_id: int,
        rank: int,
        slate_id: str,
        logging_version: str,
        target_version: str,
        is_primary_choice: bool = True,
        target_prob: float = 0.80,
        pool_size: int = 20
    ) -> ExposureRecord:
        pi_0 = self.exploration_model.get_logging_probability(is_primary_choice, candidate_pool_size=pool_size)
        p_exam = self.position_model.get_examination_probability(rank)
        joint_p = max(0.001, round(pi_0 * p_exam, 5))

        rec = ExposureRecord(
            exposure_id=exposure_id,
            request_id=request_id,
            user_id=user_id,
            item_id=item_id,
            rank=rank,
            slate_id=slate_id,
            logging_policy_version=logging_version,
            target_policy_version=target_version,
            logging_probability=pi_0,
            target_probability=target_prob,
            examination_probability=p_exam,
            joint_propensity=joint_p,
            timestamp=datetime.now(timezone.utc)
        )
        self._records.append(rec)
        return rec

    def log_exposure(
        self, exposure_id: str, user_id: str, item_id: int, rank: int, model_version: str
    ) -> ExposureRecord:
        p_exam = self.position_model.get_examination_probability(rank)
        return self.log_policy_exposure(
            exposure_id=exposure_id,
            request_id="req_compat",
            user_id=user_id,
            item_id=item_id,
            rank=rank,
            slate_id="slate_compat",
            logging_version="compat-v6.2",
            target_version=model_version,
            is_primary_choice=True
        )

    def record_response(self, exposure_id: str, item_id: int, response_type: str) -> None:
        for r in self._records:
            if r.exposure_id == exposure_id and r.item_id == item_id:
                r.observed_response = response_type
                break

    def get_records(self) -> List[ExposureRecord]:
        return self._records

    def get_logs(self) -> List[ExposureRecord]:
        return self._records


# Alias for backward compatibility
ExposureLogger = PolicyAwareExposureLogger
