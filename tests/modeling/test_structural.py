import numpy as np
import pytest

from superlig_forecast.modeling.structural import DixonColesModel, score_matrix


def test_score_matrix_is_nonnegative_and_normalized() -> None:
    matrix = score_matrix(1.8, 1.1, rho=-0.08)
    assert matrix.shape == (11, 11)
    assert np.all(matrix >= 0)
    assert matrix.sum() == pytest.approx(1.0, abs=1e-12)


def test_home_advantage_increases_home_expected_goals() -> None:
    model = DixonColesModel(home_advantage=0.2, rho=-0.05)
    home, _ = model.expected_goals(home_attack=0.1, away_defence=0.0, neutral=False)
    neutral, _ = model.expected_goals(home_attack=0.1, away_defence=0.0, neutral=True)
    assert home > neutral
