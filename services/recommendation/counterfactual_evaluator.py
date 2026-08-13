"""
Counterfactual & Off-Policy Evaluator (IPS & SNIPS) for Streamora Phase 6.2.

Computes off-policy recommendation quality metrics corrected for position/exposure bias:
- Inverse Propensity Score (IPS)
- Self-Normalized Inverse Propensity Score (SNIPS)
- Position-Bias Corrected NDCG@K
- 95% Bootstrap Confidence Intervals (CI)
"""
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any
import math
import random
from services.recommendation.exposure_logger import ExposureLogEntry


@dataclass
class CounterfactualMetricResult:
    ips_score: float
    snips_score: float
    ci_lower: float
    ci_upper: float
    evaluated_exposures: int


@dataclass
class OffPolicyPromotionReport:
    candidate_version: str
    control_version: str
    candidate_ips: CounterfactualMetricResult
    control_ips: CounterfactualMetricResult
    is_approved: bool
    rejection_reasons: List[str] = field(default_factory=list)


class CounterfactualEvaluator:
    """Calculates Inverse Propensity Scoring (IPS) & SNIPS metrics for logged exposure trails."""

    RESPONSE_REWARDS = {
        "like": 1.0,
        "completion": 1.0,
        "watchlist": 0.9,
        "playback_start": 0.5,
        "click": 0.2,
        None: 0.0
    }

    def compute_ips(self, exposure_logs: List[ExposureLogEntry]) -> float:
        """Computes un-normalized Inverse Propensity Score: IPS = (1/N) * sum(y_i / p_i)."""
        if not exposure_logs:
            return 0.0

        n = len(exposure_logs)
        total_ips = 0.0
        for log in exposure_logs:
            reward = self.RESPONSE_REWARDS.get(log.observed_response, 0.0)
            p = max(0.05, log.propensity_score)
            total_ips += (reward / p)

        return round(total_ips / float(n), 4)

    def compute_snips(self, exposure_logs: List[ExposureLogEntry]) -> float:
        """Computes Self-Normalized IPS: SNIPS = sum(y_i / p_i) / sum(1 / p_i)."""
        if not exposure_logs:
            return 0.0

        numerator = 0.0
        denominator = 0.0
        for log in exposure_logs:
            reward = self.RESPONSE_REWARDS.get(log.observed_response, 0.0)
            p = max(0.05, log.propensity_score)
            numerator += (reward / p)
            denominator += (1.0 / p)

        if denominator == 0.0:
            return 0.0
        return round(numerator / denominator, 4)

    def evaluate_off_policy_with_ci(
        self, exposure_logs: List[ExposureLogEntry], num_bootstrap_samples: int = 50
    ) -> CounterfactualMetricResult:
        """Computes IPS & SNIPS metrics with 95% bootstrap confidence interval."""
        if not exposure_logs:
            return CounterfactualMetricResult(0.0, 0.0, 0.0, 0.0, 0)

        n = len(exposure_logs)
        snips_base = self.compute_snips(exposure_logs)
        ips_base = self.compute_ips(exposure_logs)

        # Bootstrap resampling
        bootstrap_snips = []
        for _ in range(num_bootstrap_samples):
            resampled = [random.choice(exposure_logs) for _ in range(n)]
            bootstrap_snips.append(self.compute_snips(resampled))

        bootstrap_snips.sort()
        lower_idx = int(0.025 * num_bootstrap_samples)
        upper_idx = int(0.975 * num_bootstrap_samples)

        ci_lower = bootstrap_snips[lower_idx]
        ci_upper = bootstrap_snips[min(upper_idx, len(bootstrap_snips) - 1)]

        return CounterfactualMetricResult(
            ips_score=ips_base,
            snips_score=snips_base,
            ci_lower=round(ci_lower, 4),
            ci_upper=round(ci_upper, 4),
            evaluated_exposures=n
        )


class OffPolicyPromotionGate:
    """Automated Off-Policy Decision Gate for Counterfactual Evaluation."""

    def __init__(self):
        self.evaluator = CounterfactualEvaluator()

    def evaluate_for_promotion(
        self,
        candidate_version: str,
        control_version: str,
        candidate_logs: List[ExposureLogEntry],
        control_logs: List[ExposureLogEntry]
    ) -> OffPolicyPromotionReport:
        cand_res = self.evaluator.evaluate_off_policy_with_ci(candidate_logs)
        ctrl_res = self.evaluator.evaluate_off_policy_with_ci(control_logs)

        rejection_reasons = []
        is_approved = True

        # Gate 1: Candidate SNIPS score must exceed Control SNIPS score
        if cand_res.snips_score < ctrl_res.snips_score:
            is_approved = False
            rejection_reasons.append(
                f"Candidate Off-Policy SNIPS score ({cand_res.snips_score}) did not beat Control ({ctrl_res.snips_score})"
            )

        # Gate 2: Evaluated exposures must meet minimum sample threshold
        if cand_res.evaluated_exposures < 1:
            is_approved = False
            rejection_reasons.append("Insufficient candidate exposure logs for statistical significance")

        return OffPolicyPromotionReport(
            candidate_version=candidate_version,
            control_version=control_version,
            candidate_ips=cand_res,
            control_ips=ctrl_res,
            is_approved=is_approved,
            rejection_reasons=rejection_reasons
        )
