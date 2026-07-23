"""Dixon–Coles structural score probabilities."""

from dataclasses import dataclass
from math import exp, factorial
from typing import cast

import numpy as np
import numpy.typing as npt


def dixon_coles_tau(
    home: int, away: int, lambda_home: float, lambda_away: float, rho: float
) -> float:
    if (home, away) == (0, 0):
        return 1.0 - lambda_home * lambda_away * rho
    if (home, away) == (0, 1):
        return 1.0 + lambda_home * rho
    if (home, away) == (1, 0):
        return 1.0 + lambda_away * rho
    if (home, away) == (1, 1):
        return 1.0 - rho
    return 1.0


def score_matrix(
    lambda_home: float, lambda_away: float, rho: float, max_goals: int = 10
) -> npt.NDArray[np.float64]:
    lambda_home = float(np.clip(lambda_home, 0.05, 6.0))
    lambda_away = float(np.clip(lambda_away, 0.05, 6.0))
    home = np.array(
        [exp(-lambda_home) * lambda_home**goals / factorial(goals) for goals in range(max_goals + 1)]
    )
    away = np.array(
        [exp(-lambda_away) * lambda_away**goals / factorial(goals) for goals in range(max_goals + 1)]
    )
    matrix = np.outer(home, away)
    for home_goals in range(2):
        for away_goals in range(2):
            matrix[home_goals, away_goals] *= dixon_coles_tau(
                home_goals, away_goals, lambda_home, lambda_away, rho
            )
    return cast(npt.NDArray[np.float64], matrix / matrix.sum())


@dataclass(frozen=True)
class DixonColesModel:
    home_advantage: float
    rho: float
    base_log_rate: float = 0.2

    def expected_goals(
        self,
        *,
        home_attack: float,
        away_defence: float,
        neutral: bool,
        away_attack: float = 0.0,
        home_defence: float = 0.0,
    ) -> tuple[float, float]:
        advantage = 0.0 if neutral else self.home_advantage
        home = np.exp(self.base_log_rate + advantage + home_attack + away_defence)
        away = np.exp(self.base_log_rate + away_attack + home_defence)
        return float(home), float(away)

    def predict_score_matrix(
        self,
        *,
        home_attack: float,
        away_defence: float,
        neutral: bool,
        away_attack: float = 0.0,
        home_defence: float = 0.0,
    ) -> npt.NDArray[np.float64]:
        home, away = self.expected_goals(
            home_attack=home_attack,
            away_defence=away_defence,
            neutral=neutral,
            away_attack=away_attack,
            home_defence=home_defence,
        )
        return score_matrix(home, away, self.rho)
