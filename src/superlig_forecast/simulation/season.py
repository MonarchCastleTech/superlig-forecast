"""Chunked vectorized Monte Carlo season simulation."""

import math
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from superlig_forecast.simulation.rules import LeagueRules


@dataclass(frozen=True)
class FixtureForecast:
    home_index: int
    away_index: int
    score_matrix: npt.NDArray[np.float64]


@dataclass(frozen=True)
class SimulationResult:
    champion_counts: dict[str, int]
    n_simulations: int
    draw_count: int
    decisive_count: int
    total_points: int


class SeasonSimulator:
    def __init__(self, team_ids: tuple[str, ...], rules: LeagueRules) -> None:
        self.team_ids = team_ids
        self.rules = rules

    def simulate(
        self,
        fixtures: list[FixtureForecast],
        *,
        n: int,
        seed: int,
        chunk_size: int = 100_000,
    ) -> SimulationResult:
        rng = np.random.default_rng(seed)
        champions = np.zeros(len(self.team_ids), dtype=np.int64)
        total_draws = total_decisive = total_points = 0
        completed = 0
        while completed < n:
            size = min(chunk_size, n - completed)
            points = np.zeros((size, len(self.team_ids)), dtype=np.int16)
            goals_for = np.zeros_like(points)
            goals_against = np.zeros_like(points)
            for fixture in fixtures:
                side = fixture.score_matrix.shape[0]
                flat = rng.choice(fixture.score_matrix.size, size=size, p=fixture.score_matrix.ravel())
                home_goals, away_goals = flat // side, flat % side
                draw = home_goals == away_goals
                home_win = home_goals > away_goals
                away_win = home_goals < away_goals
                points[:, fixture.home_index] += (
                    home_win * self.rules.win_points + draw * self.rules.draw_points
                )
                points[:, fixture.away_index] += (
                    away_win * self.rules.win_points + draw * self.rules.draw_points
                )
                goals_for[:, fixture.home_index] += home_goals
                goals_against[:, fixture.home_index] += away_goals
                goals_for[:, fixture.away_index] += away_goals
                goals_against[:, fixture.away_index] += home_goals
                total_draws += int(draw.sum())
                total_decisive += int((~draw).sum())
            goal_difference = goals_for - goals_against
            ranking_score = points.astype(np.int64) * 1_000_000 + goal_difference * 1_000 + goals_for
            winner = np.argmax(ranking_score, axis=1)
            champions += np.bincount(winner, minlength=len(self.team_ids))
            total_points += int(points.sum())
            completed += size
        return SimulationResult(
            dict(zip(self.team_ids, champions.tolist(), strict=True)),
            n,
            total_draws,
            total_decisive,
            total_points,
        )

    @staticmethod
    def half_width(champion_count: int, n: int) -> float:
        probability = champion_count / n
        return 1.96 * math.sqrt(probability * (1 - probability) / n)
