from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from superlig_forecast.domain import OddsObservation
from superlig_forecast.modeling.calibration import apply_temperature
from superlig_forecast.modeling.hybrid import HybridModel, one_x_two_from_matrix
from superlig_forecast.modeling.market import MarketConsensus, remove_margin
from superlig_forecast.modeling.structural import score_matrix


def test_power_devig_returns_probabilities_summing_to_one() -> None:
    fair = remove_margin(np.array([1.72, 3.70, 5.20]))
    assert fair.sum() == pytest.approx(1.0)
    assert np.all(fair > 0)


def test_market_consensus_ignores_observation_after_cutoff() -> None:
    cutoff = datetime(2026, 8, 7, tzinfo=UTC)
    rows = [
        OddsObservation(
            match_source_key="m1",
            provider="A",
            observed_at=cutoff - timedelta(hours=1),
            home_odds=1.8,
            draw_odds=3.5,
            away_odds=4.8,
        ),
        OddsObservation(
            match_source_key="m1",
            provider="B",
            observed_at=cutoff + timedelta(hours=1),
            home_odds=1.6,
            draw_odds=3.7,
            away_odds=5.5,
        ),
    ]
    consensus = MarketConsensus.from_observations(rows, cutoff)
    assert consensus is not None
    assert consensus.latest_observed_at <= cutoff


def test_hybrid_keeps_score_and_outcome_probabilities_coherent() -> None:
    matrix = score_matrix(1.7, 1.0, -0.05)
    calibrated = apply_temperature(matrix, 1.1)
    forecast = HybridModel().predict(calibrated, market=None)
    assert forecast.outcome_probabilities == pytest.approx(one_x_two_from_matrix(forecast.matrix))
    assert forecast.matrix.sum() == pytest.approx(1.0)
