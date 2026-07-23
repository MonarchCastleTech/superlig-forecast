"""Leakage-safe preseason backtesting for full league-table distributions."""

from dataclasses import dataclass
import math

import numpy as np

from superlig_forecast.backtest.walk_forward import BacktestMatch
from superlig_forecast.modeling.team_strength import TeamStrengthModel
from superlig_forecast.simulation.rules import LeagueRules
from superlig_forecast.simulation.season import FixtureForecast, SeasonSimulator


@dataclass(frozen=True)
class ActualTableRow:
    team: str
    position: int
    points: int
    goal_difference: int
    goals_for: int


@dataclass(frozen=True)
class TeamPositionBacktest:
    team: str
    actual_position: int
    expected_position: float
    median_position: int
    most_likely_position: int
    actual_position_probability: float
    expected_points: float
    expected_goal_difference: float
    position_probabilities: tuple[float, ...]


@dataclass(frozen=True)
class PositionScoreSummary:
    position_log_loss: float
    uniform_log_loss: float
    position_brier: float
    uniform_brier: float
    mean_absolute_position_error: float
    uniform_mean_absolute_position_error: float
    rank_correlation: float
    mean_actual_position_probability: float


@dataclass(frozen=True)
class PositionFoldSummary:
    season: int
    team_count: int
    match_count: int
    simulations: int
    scores: PositionScoreSummary
    teams: tuple[TeamPositionBacktest, ...]


@dataclass(frozen=True)
class PositionBacktestReport:
    folds: tuple[PositionFoldSummary, ...]
    aggregate: PositionScoreSummary
    simulations_per_fold: int

    @property
    def fold_count(self) -> int:
        return len(self.folds)


def actual_table(matches: list[BacktestMatch]) -> tuple[ActualTableRow, ...]:
    """Reconstruct a table with the simulator's points/GD/GF tie-break order."""

    teams = sorted({team for match in matches for team in (match.home_team, match.away_team)})
    stats = {team: [0, 0, 0] for team in teams}
    for match in matches:
        home = stats[match.home_team]
        away = stats[match.away_team]
        home[1] += match.home_goals
        home[2] += match.away_goals
        away[1] += match.away_goals
        away[2] += match.home_goals
        if match.home_goals > match.away_goals:
            home[0] += 3
        elif match.home_goals < match.away_goals:
            away[0] += 3
        else:
            home[0] += 1
            away[0] += 1

    order = sorted(
        teams,
        key=lambda team: (
            -stats[team][0],
            -(stats[team][1] - stats[team][2]),
            -stats[team][1],
            team,
        ),
    )
    return tuple(
        ActualTableRow(
            team,
            position,
            stats[team][0],
            stats[team][1] - stats[team][2],
            stats[team][1],
        )
        for position, team in enumerate(order, start=1)
    )


def _score_rows(
    rows: list[TeamPositionBacktest],
    *,
    team_count: int,
) -> PositionScoreSummary:
    log_losses = [-math.log(max(row.actual_position_probability, 1e-12)) for row in rows]
    brier_scores: list[float] = []
    absolute_errors: list[float] = []
    actual_positions: list[float] = []
    expected_positions: list[float] = []
    for row in rows:
        target = np.zeros(team_count, dtype=float)
        target[row.actual_position - 1] = 1.0
        probabilities = np.asarray(row.position_probabilities)
        brier_scores.append(float(np.sum((probabilities - target) ** 2)))
        absolute_errors.append(abs(row.expected_position - row.actual_position))
        actual_positions.append(float(row.actual_position))
        expected_positions.append(row.expected_position)
    midpoint = (team_count + 1) / 2
    uniform_mae = float(np.mean([abs(midpoint - position) for position in actual_positions]))
    correlation = float(np.corrcoef(actual_positions, expected_positions)[0, 1])
    if not math.isfinite(correlation):
        correlation = 0.0
    return PositionScoreSummary(
        position_log_loss=float(np.mean(log_losses)),
        uniform_log_loss=math.log(team_count),
        position_brier=float(np.mean(brier_scores)),
        uniform_brier=1.0 - 1.0 / team_count,
        mean_absolute_position_error=float(np.mean(absolute_errors)),
        uniform_mean_absolute_position_error=uniform_mae,
        rank_correlation=correlation,
        mean_actual_position_probability=float(
            np.mean([row.actual_position_probability for row in rows])
        ),
    )


def _aggregate_scores(folds: list[PositionFoldSummary]) -> PositionScoreSummary:
    weights = np.asarray([fold.team_count for fold in folds], dtype=float)
    weights /= weights.sum()

    def weighted(name: str) -> float:
        return float(
            np.dot(
                weights,
                [float(getattr(fold.scores, name)) for fold in folds],
            )
        )

    return PositionScoreSummary(
        position_log_loss=weighted("position_log_loss"),
        uniform_log_loss=weighted("uniform_log_loss"),
        position_brier=weighted("position_brier"),
        uniform_brier=weighted("uniform_brier"),
        mean_absolute_position_error=weighted("mean_absolute_position_error"),
        uniform_mean_absolute_position_error=weighted("uniform_mean_absolute_position_error"),
        rank_correlation=weighted("rank_correlation"),
        mean_actual_position_probability=weighted("mean_actual_position_probability"),
    )


def run_position_backtest(
    matches: list[BacktestMatch],
    *,
    start_season: int,
    end_season: int,
    simulations: int = 20_000,
    seed: int = 202627,
    chunk_size: int = 20_000,
) -> PositionBacktestReport:
    """Simulate each target season using a model fitted only on earlier seasons."""

    folds: list[PositionFoldSummary] = []
    for season in range(start_season, end_season + 1):
        training = [match for match in matches if match.season < season]
        test = [match for match in matches if match.season == season]
        if not training or not test:
            raise ValueError(f"season {season} lacks strict train/test coverage")

        teams = tuple(
            sorted({team for match in test for team in (match.home_team, match.away_team)})
        )
        team_index = {team: index for index, team in enumerate(teams)}
        model = TeamStrengthModel.fit(
            [match.played() for match in training],
            before_season=season,
        )
        fixtures = [
            FixtureForecast(
                team_index[match.home_team],
                team_index[match.away_team],
                model.predict_score_matrix(match.home_team, match.away_team),
            )
            for match in test
        ]
        result = SeasonSimulator(teams, LeagueRules.default()).simulate(
            fixtures,
            n=simulations,
            seed=seed + season,
            chunk_size=chunk_size,
        )
        actual = {row.team: row for row in actual_table(test)}
        alpha = 0.5
        denominator = simulations + alpha * len(teams)
        rows: list[TeamPositionBacktest] = []
        for team in teams:
            counts = np.asarray(result.position_counts[team], dtype=float)
            probabilities = (counts + alpha) / denominator
            positions = np.arange(1, len(teams) + 1, dtype=float)
            cumulative = np.cumsum(probabilities)
            actual_position = actual[team].position
            rows.append(
                TeamPositionBacktest(
                    team=team,
                    actual_position=actual_position,
                    expected_position=float(np.dot(positions, probabilities)),
                    median_position=int(np.searchsorted(cumulative, 0.5) + 1),
                    most_likely_position=int(np.argmax(probabilities) + 1),
                    actual_position_probability=float(probabilities[actual_position - 1]),
                    expected_points=result.point_sums[team] / simulations,
                    expected_goal_difference=(result.goal_difference_sums[team] / simulations),
                    position_probabilities=tuple(float(value) for value in probabilities),
                )
            )
        rows.sort(key=lambda row: row.actual_position)
        folds.append(
            PositionFoldSummary(
                season=season,
                team_count=len(teams),
                match_count=len(test),
                simulations=simulations,
                scores=_score_rows(rows, team_count=len(teams)),
                teams=tuple(rows),
            )
        )

    return PositionBacktestReport(
        tuple(folds),
        _aggregate_scores(folds),
        simulations,
    )
