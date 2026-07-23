from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from superlig_forecast.domain import (
    ForecastMode,
    MatchForecast,
    MatchRecord,
    OddsObservation,
    PlayerValuation,
)


def test_match_record_exposes_unfinished_state() -> None:
    record = MatchRecord(
        match_id="tff:317790",
        competition_id="TR1",
        season="2026-27",
        kickoff=datetime(2026, 8, 8, 18, 0, tzinfo=UTC),
        home_club_id="club:1",
        away_club_id="club:2",
        home_club_name="Galatasaray A.Ş.",
        away_club_name="Çorum FK",
        home_goals=None,
        away_goals=None,
        observed_at=datetime(2026, 7, 23, tzinfo=UTC),
    )

    assert record.is_finished is False
    assert ForecastMode.EXPECTED_LINEUP.value == "expected_lineup"


def test_match_record_rejects_naive_kickoff() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        MatchRecord(
            match_id="tff:317790",
            competition_id="TR1",
            season="2026-27",
            kickoff=datetime(2026, 8, 8, 18, 0),
            home_club_id="club:1",
            away_club_id="club:2",
            home_club_name="Galatasaray A.Ş.",
            away_club_name="Çorum FK",
            home_goals=None,
            away_goals=None,
            observed_at=datetime(2026, 7, 23, tzinfo=UTC),
        )


def test_player_valuation_rejects_negative_market_value() -> None:
    with pytest.raises(ValidationError, match="greater than or equal to 0"):
        PlayerValuation(
            player_id="player:10",
            club_id="club:1",
            effective_date=datetime(2026, 7, 1, tzinfo=UTC),
            market_value_eur=-1,
            observed_at=datetime(2026, 7, 1, tzinfo=UTC),
        )


def test_odds_observation_requires_decimal_odds_above_one() -> None:
    with pytest.raises(ValidationError, match="greater than 1"):
        OddsObservation(
            match_source_key="2026-08-08|Galatasaray|Çorum FK",
            provider="Example",
            observed_at=datetime(2026, 8, 7, tzinfo=UTC),
            home_odds=1.0,
            draw_odds=3.8,
            away_odds=5.2,
        )


def test_match_forecast_probabilities_must_sum_to_one() -> None:
    with pytest.raises(ValidationError, match="sum to 1"):
        MatchForecast(
            match_id="tff:317790",
            mode=ForecastMode.EXPECTED_LINEUP,
            cutoff=datetime(2026, 8, 7, 18, 0, tzinfo=UTC),
            score_probabilities=((0.2, 0.2), (0.2, 0.2)),
            home_probability=0.4,
            draw_probability=0.3,
            away_probability=0.4,
            model_version="test",
            data_hash="abc123",
        )
