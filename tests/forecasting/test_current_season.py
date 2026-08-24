from datetime import date

import numpy as np

from superlig_forecast.data.structured_sources import StructuredMatch
from superlig_forecast.data.transfermarkt_live import CurrentSquadValue
from superlig_forecast.forecasting.current_season import (
    model_from_artifact,
    prepare_current_season,
    prepare_current_season_from_model,
)
from superlig_forecast.modeling.team_strength import PlayedMatch, TeamRates


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
    assert all(item.predicted for item in prepared.expectations)


def test_model_artifact_round_trips_without_the_historical_warehouse() -> None:
    model = model_from_artifact(
        {
            "league_home_goals": 1.5,
            "league_away_goals": 1.2,
            "rho": -0.05,
            "team_rates": {
                "a": {
                    "home_attack": 1.2,
                    "home_defence": 0.9,
                    "away_attack": 1.1,
                    "away_defence": 0.8,
                }
            },
        }
    )

    assert model.league_home_goals == 1.5
    assert model.rates["a"] == TeamRates(1.2, 0.9, 1.1, 0.8)


def test_completed_matches_seed_table_and_are_not_resimulated() -> None:
    model = model_from_artifact(
        {
            "league_home_goals": 1.5,
            "league_away_goals": 1.2,
            "rho": -0.05,
            "team_rates": {},
        }
    )
    squads = [
        CurrentSquadValue(1, "A SK", 25, 100_000_000),
        CurrentSquadValue(2, "B SK", 25, 50_000_000),
    ]
    played = [
        StructuredMatch("2026-08-08", "A", "B", 2, 0, "finished"),
    ]

    prepared = prepare_current_season_from_model(model, squads, played_matches=played)

    assert len(prepared.fixtures) == 1
    assert prepared.starting_table["A SK"].points == 3
    assert prepared.starting_table["A SK"].goals_for == 2
    assert prepared.starting_table["B SK"].goals_against == 2
