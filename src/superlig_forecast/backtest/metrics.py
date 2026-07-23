"""Proper scoring rules and model comparisons."""

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt


def brier_score_multiclass(
    probabilities: npt.NDArray[np.float64], target: npt.NDArray[np.int64]
) -> float:
    observed = np.eye(probabilities.shape[1])[target]
    return float(np.mean(np.sum((probabilities - observed) ** 2, axis=1)))


@dataclass(frozen=True)
class MetricComparison:
    hybrid_log_loss: float
    hybrid_brier: float
    best_non_market_log_loss: float
    best_non_market_brier: float
    market_log_loss: float | None
    market_brier: float | None
