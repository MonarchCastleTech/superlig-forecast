from datetime import date
from pathlib import Path

import duckdb

from superlig_forecast.backtest.walk_forward import (
    BacktestMatch,
    load_backtest_matches,
    run_walk_forward,
)


def test_walk_forward_returns_one_strict_fold_per_requested_season() -> None:
    matches = [
        BacktestMatch(date(2000, 8, 1), 2000, "A", "B", 2, 0, 1.8, 3.4, 4.5),
        BacktestMatch(date(2000, 8, 8), 2000, "B", "A", 0, 1, 3.5, 3.2, 2.0),
        BacktestMatch(date(2001, 8, 1), 2001, "A", "B", 1, 0, 1.9, 3.3, 4.2),
        BacktestMatch(date(2001, 8, 8), 2001, "B", "A", 1, 1, 3.3, 3.1, 2.1),
        BacktestMatch(date(2002, 8, 1), 2002, "A", "B", 3, 0, 1.7, 3.5, 5.0),
        BacktestMatch(date(2002, 8, 8), 2002, "B", "A", 0, 2, 4.0, 3.3, 1.9),
    ]

    report = run_walk_forward(matches, start_season=2001, end_season=2002)

    assert report.fold_count == 2
    assert [fold.season for fold in report.folds] == [2001, 2002]
    assert report.match_count == 4
    assert 0.0 < report.aggregate.hybrid_log_loss < 5.0
    assert 0.0 <= report.aggregate.hybrid_brier <= 2.0


def test_load_backtest_matches_reads_normalized_warehouse(tmp_path: Path) -> None:
    path = tmp_path / "model.duckdb"
    with duckdb.connect(str(path)) as connection:
        connection.execute(
            """
            create table training_matches as
            select 'x' match_id, date '2025-08-01' date, 2025 season,
                   'A' home_team, 'B' away_team, 1 home_goals, 0 away_goals,
                   2.0 home_odds, 3.0 draw_odds, 4.0 away_odds,
                   'fixture' as source
            """
        )

    matches = load_backtest_matches(path)

    assert matches == [BacktestMatch(date(2025, 8, 1), 2025, "A", "B", 1, 0, 2.0, 3.0, 4.0)]
