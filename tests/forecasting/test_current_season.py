from datetime import date

import numpy as np

from superlig_forecast.data.transfermarkt_live import CurrentSquadValue
from superlig_forecast.forecasting.current_season import prepare_current_season
from superlig_forecast.modeling.team_strength import PlayedMatch


def test_prepare_current_season_builds_double_round_robin_with_value_shift() -> None:
    history = [
        PlayedMatch(date(2025, 8, 1), 2025, "A", "B", 2, 0),
        PlayedMatch(date(2025, 8, 2), 2025, "C", "D", 1, 1),
    ]
    squads = [
        CurrentSquadValue(1, "A", 25, 100_000_000),
        CurrentSquadValue(2, "B", 25, 50_000_000),
        CurrentSquadValue(3, "C", 25, 25_000_000),
        CurrentSquadValue(4, "D", 25, 10_000_000),
    ]

    prepared = prepare_current_season(history, squads, season=2026)

    assert prepared.team_ids == ("A", "B", "C", "D")
    assert len(prepared.fixtures) == 12
    assert all(np.isclose(fixture.score_matrix.sum(), 1.0) for fixture in prepared.fixtures)
    assert all(
        np.isclose(
            item.home_win_probability + item.draw_probability + item.away_win_probability,
            1.0,
        )
        for item in prepared.expectations
    )
