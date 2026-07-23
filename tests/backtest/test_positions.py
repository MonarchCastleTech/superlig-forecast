from datetime import date
import math

import pytest

from superlig_forecast.backtest.positions import (
    actual_table,
    run_position_backtest,
)
from superlig_forecast.backtest.walk_forward import BacktestMatch


def _season(season: int) -> list[BacktestMatch]:
    teams = ("A", "B", "C", "D")
    strength = {"A": 4, "B": 3, "C": 2, "D": 1}
    matches: list[BacktestMatch] = []
    day = 1
    for home in teams:
        for away in teams:
            if home == away:
                continue
            home_goals, away_goals = (2, 0) if strength[home] > strength[away] else (0, 2)
            matches.append(
                BacktestMatch(
                    date(season, 1, day),
                    season,
                    home,
                    away,
                    home_goals,
                    away_goals,
                )
            )
            day += 1
    return matches


def test_actual_table_reconstructs_rank_from_results() -> None:
    table = actual_table(_season(2021))

    assert [row.team for row in table] == ["A", "B", "C", "D"]
    assert [row.position for row in table] == [1, 2, 3, 4]
    assert table[0].points == 18
    assert table[-1].goal_difference < 0


def test_position_backtest_scores_complete_distributions() -> None:
    report = run_position_backtest(
        _season(2020) + _season(2021),
        start_season=2021,
        end_season=2021,
        simulations=2_000,
        seed=42,
        chunk_size=250,
    )

    assert report.fold_count == 1
    fold = report.folds[0]
    assert fold.team_count == 4
    assert fold.match_count == 12
    assert {row.actual_position for row in fold.teams} == {1, 2, 3, 4}
    assert all(sum(row.position_probabilities) == pytest.approx(1.0) for row in fold.teams)
    assert all(1 <= row.expected_position <= 4 for row in fold.teams)
    assert math.isfinite(report.aggregate.position_log_loss)
    assert report.aggregate.uniform_log_loss == pytest.approx(math.log(4))
    assert report.aggregate.position_brier >= 0
    assert report.aggregate.mean_absolute_position_error >= 0


def test_position_backtest_is_deterministic_for_a_fixed_seed() -> None:
    kwargs = {
        "start_season": 2021,
        "end_season": 2021,
        "simulations": 500,
        "seed": 7,
        "chunk_size": 100,
    }
    matches = _season(2020) + _season(2021)

    first = run_position_backtest(matches, **kwargs)
    second = run_position_backtest(matches, **kwargs)

    assert first == second
