"""Coherent structural and market probability blending."""

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from superlig_forecast.modeling.market import MarketConsensus


def one_x_two_from_matrix(matrix: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    return np.array(
        [np.tril(matrix, -1).sum(), np.trace(matrix), np.triu(matrix, 1).sum()],
        dtype=float,
    )


@dataclass(frozen=True)
class HybridForecast:
    matrix: npt.NDArray[np.float64]
    outcome_probabilities: npt.NDArray[np.float64]


class HybridModel:
    def __init__(self, market_weight: float = 0.35) -> None:
        self.market_weight = market_weight

    def predict(
        self,
        structural_matrix: npt.NDArray[np.float64],
        market: MarketConsensus | None,
    ) -> HybridForecast:
        matrix = structural_matrix / structural_matrix.sum()
        if market is not None:
            base = one_x_two_from_matrix(matrix)
            target = (1 - self.market_weight) * base + self.market_weight * market.probabilities
            masks = [
                np.tril(np.ones_like(matrix), -1),
                np.eye(matrix.shape[0]),
                np.triu(np.ones_like(matrix), 1),
            ]
            adjusted = np.zeros_like(matrix)
            for probability, current, mask in zip(target, base, masks, strict=True):
                adjusted += matrix * mask * (probability / current)
            matrix = adjusted / adjusted.sum()
        typed = matrix
        return HybridForecast(typed, one_x_two_from_matrix(typed))
