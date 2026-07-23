import numpy as np
import pytest

from superlig_forecast.backtest.metrics import MetricComparison, brier_score_multiclass
from superlig_forecast.backtest.runner import AcceptanceGate
from superlig_forecast.backtest.splits import walk_forward_folds


def seasons(start: int, end: int) -> list[str]:
    return [f"{year:04d}-{(year + 1) % 100:02d}" for year in range(start, end + 1)]


def test_twenty_expanding_folds_train_only_on_the_past() -> None:
    folds = walk_forward_folds(seasons(2000, 2025), warmup_end="2005-06")
    assert len(folds) == 20
    assert folds[0].test_season == "2006-07"
    assert all(max(fold.train_seasons) < fold.test_season for fold in folds)


def test_multiclass_brier_score() -> None:
    probabilities = np.array([[0.7, 0.2, 0.1]])
    assert brier_score_multiclass(probabilities, np.array([0])) == pytest.approx(0.14)


def test_gate_fails_when_brier_does_not_improve() -> None:
    result = AcceptanceGate.evaluate(
        MetricComparison(
            hybrid_log_loss=0.90,
            hybrid_brier=0.62,
            best_non_market_log_loss=0.95,
            best_non_market_brier=0.60,
            market_log_loss=0.90,
            market_brier=0.61,
        )
    )
    assert result.passed is False
    assert any("Brier" in message for message in result.failures)
