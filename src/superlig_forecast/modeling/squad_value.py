"""Conservative player-market-value adjustment for current squads."""

from math import exp, log

import numpy as np


def adjust_expected_goals_for_value(
    home_expected_goals: float,
    away_expected_goals: float,
    *,
    home_value_eur: int,
    away_value_eur: int,
    coefficient: float = 0.1,
) -> tuple[float, float]:
    """Apply a symmetric log-value shift while preserving plausible goal rates."""

    ratio = (home_value_eur + 1_000_000) / (away_value_eur + 1_000_000)
    multiplier = exp(0.5 * coefficient * log(ratio))
    home = float(np.clip(home_expected_goals * multiplier, 0.2, 4.5))
    away = float(np.clip(away_expected_goals / multiplier, 0.2, 4.5))
    return home, away
