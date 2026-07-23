from datetime import UTC, datetime

import polars as pl
import pytest

from superlig_forecast.features.lineups import expected_start_probabilities
from superlig_forecast.features.point_in_time import asof_join
from superlig_forecast.features.promotion import PromotionPrior
from superlig_forecast.features.values import normalize_market_values


def test_asof_join_never_uses_later_value() -> None:
    matches = pl.DataFrame({"player_id": [1], "cutoff": [datetime(2025, 6, 1, tzinfo=UTC)]})
    values = pl.DataFrame(
        {
            "player_id": [1, 1],
            "date": [
                datetime(2025, 3, 1, tzinfo=UTC),
                datetime(2025, 7, 1, tzinfo=UTC),
            ],
            "value": [8, 12],
        }
    )
    result = asof_join(matches, values, by=["player_id"], left_time="cutoff", right_time="date")
    assert result["value"].item() == 8


def test_expected_start_probabilities_sum_to_eleven() -> None:
    probabilities = expected_start_probabilities([10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 1, 1, 1])
    assert sum(probabilities) == pytest.approx(11.0)
    assert all(0 <= value <= 1 for value in probabilities)


def test_promotion_prior_uses_only_earlier_seasons() -> None:
    history = pl.DataFrame(
        {"season": ["2016-17", "2017-18", "2018-19"], "translation": [-0.4, -0.2, 0.9]}
    )
    prior = PromotionPrior.fit(history, training_end="2017-18")
    assert prior.source_seasons == ("2016-17", "2017-18")
    assert prior.division_offset == pytest.approx(-0.3)


def test_market_values_are_normalized_within_season_and_position() -> None:
    frame = pl.DataFrame(
        {
            "season": ["2025-26"] * 3,
            "position": ["Attack"] * 3,
            "market_value_eur": [1_000_000, 2_000_000, 4_000_000],
        }
    )
    result = normalize_market_values(frame)
    assert result["value_score"].is_finite().all()
    assert result["value_score"].median() == pytest.approx(0.0)
