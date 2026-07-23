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
    position_counts: dict[str, tuple[int, ...]]
    point_sums: dict[str, int]
    goal_difference_sums: dict[str, int]
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
        return self.simulate_checkpoints(
            fixtures,
            checkpoints=(n,),
            seed=seed,
            chunk_size=chunk_size,
        )[n]

    def simulate_checkpoints(
        self,
        fixtures: list[FixtureForecast],
        *,
        checkpoints: tuple[int, ...],
        seed: int,
        chunk_size: int = 100_000,
    ) -> dict[int, SimulationResult]:
        """Run once and snapshot cumulative Monte Carlo convergence."""

        if not checkpoints or any(value <= 0 for value in checkpoints):
            raise ValueError("checkpoints must contain positive simulation counts")
        ordered = tuple(sorted(set(checkpoints)))
        rng = np.random.default_rng(seed)
        team_count = len(self.team_ids)
        position_counts = np.zeros((team_count, team_count), dtype=np.int64)
        point_sums = np.zeros(team_count, dtype=np.int64)
        goal_difference_sums = np.zeros(team_count, dtype=np.int64)
        total_draws = total_decisive = total_points = 0
        completed = 0
        results: dict[int, SimulationResult] = {}
        for checkpoint in ordered:
            while completed < checkpoint:
                size = min(chunk_size, checkpoint - completed)
                points = np.zeros((size, len(self.team_ids)), dtype=np.int16)
                goals_for = np.zeros_like(points)
                goals_against = np.zeros_like(points)
                for fixture in fixtures:
                    side = fixture.score_matrix.shape[0]
                    flat = rng.choice(
                        fixture.score_matrix.size, size=size, p=fixture.score_matrix.ravel()
                    )
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
                ranking_score = (
                    points.astype(np.int64) * 1_000_000 + goal_difference * 1_000 + goals_for
                )
                order = np.argsort(-ranking_score, axis=1, kind="stable")
                for position in range(team_count):
                    position_counts[:, position] += np.bincount(
                        order[:, position],
                        minlength=team_count,
                    )
                point_sums += points.sum(axis=0, dtype=np.int64)
                goal_difference_sums += goal_difference.sum(axis=0, dtype=np.int64)
                total_points += int(points.sum())
                completed += size
            results[checkpoint] = SimulationResult(
                dict(
                    zip(
                        self.team_ids,
                        position_counts[:, 0].tolist(),
                        strict=True,
                    )
                ),
                {
                    team: tuple(int(value) for value in position_counts[index])
                    for index, team in enumerate(self.team_ids)
                },
                dict(zip(self.team_ids, point_sums.tolist(), strict=True)),
                dict(
                    zip(
                        self.team_ids,
                        goal_difference_sums.tolist(),
                        strict=True,
                    )
                ),
                checkpoint,
                total_draws,
                total_decisive,
                total_points,
            )
        return results

    @staticmethod
    def half_width(champion_count: int, n: int) -> float:
        probability = champion_count / n
        return 1.96 * math.sqrt(probability * (1 - probability) / n)
