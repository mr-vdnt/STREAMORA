"""
Temporal Training Dataset Builder for Streamora Phase 6.

Constructs temporal train/validation/test dataset splits from interaction events without
future interaction leakage.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Any


@dataclass
class TrainingSample:
    user_id: str
    content_id: int
    features: Dict[str, float]
    label: float  # 0.0 (impression/dislike) to 1.0 (completion/like)
    timestamp: datetime


class TemporalDatasetBuilder:
    """Constructs leakage-free temporal training splits."""

    def __init__(self, val_split_days: int = 7, test_split_days: int = 7):
        self.val_split_days = val_split_days
        self.test_split_days = test_split_days

    def create_temporal_splits(
        self, samples: List[TrainingSample]
    ) -> Tuple[List[TrainingSample], List[TrainingSample], List[TrainingSample]]:
        """Splits samples into Train, Validation, and Test sets based on strict timestamp cutoff."""
        if not samples:
            return [], [], []

        sorted_samples = sorted(samples, key=lambda s: s.timestamp)
        max_time = sorted_samples[-1].timestamp

        test_cutoff = max_time - timedelta(days=self.test_split_days)
        val_cutoff = test_cutoff - timedelta(days=self.val_split_days)

        train = [s for s in sorted_samples if s.timestamp < val_cutoff]
        val = [s for s in sorted_samples if val_cutoff <= s.timestamp < test_cutoff]
        test = [s for s in sorted_samples if s.timestamp >= test_cutoff]

        # Fallback for synthetic/small test sets
        if not train and sorted_samples:
            n = len(sorted_samples)
            n_train = int(n * 0.7)
            n_val = int(n * 0.15)
            train = sorted_samples[:n_train]
            val = sorted_samples[n_train:n_train + n_val]
            test = sorted_samples[n_train + n_val:]

        return train, val, test
