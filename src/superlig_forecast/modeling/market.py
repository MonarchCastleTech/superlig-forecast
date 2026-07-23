"""Bookmaker margin removal and cutoff-safe consensus."""

from dataclasses import dataclass
from datetime import datetime
from typing import cast

import numpy as np
import numpy.typing as npt

from superlig_forecast.domain import OddsObservation


def remove_margin(decimal_odds: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    if np.any(decimal_odds <= 1.0):
        raise ValueError("decimal odds must exceed 1")
    inverse = 1.0 / decimal_odds
    low, high = 0.01, 10.0
    for _ in range(100):
        power = (low + high) / 2
        if np.power(inverse, power).sum() > 1:
            low = power
        else:
            high = power
    fair = np.power(inverse, high)
    return cast(npt.NDArray[np.float64], fair / fair.sum())


@dataclass(frozen=True)
class MarketConsensus:
    probabilities: npt.NDArray[np.float64]
    latest_observed_at: datetime
    providers: tuple[str, ...]

    @classmethod
    def from_observations(
        cls, observations: list[OddsObservation], cutoff: datetime
    ) -> "MarketConsensus | None":
        eligible = [item for item in observations if item.observed_at <= cutoff]
        if not eligible:
            return None
        probabilities = [
            remove_margin(np.array([item.home_odds, item.draw_odds, item.away_odds]))
            for item in eligible
        ]
        consensus = np.mean(probabilities, axis=0)
        return cls(
            consensus / consensus.sum(),
            max(item.observed_at for item in eligible),
            tuple(sorted({item.provider for item in eligible})),
        )
