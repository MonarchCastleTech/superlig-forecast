import pytest

from superlig_forecast.data.coverage import market_eligibility


def test_market_eligibility_requires_eighty_percent() -> None:
    result = market_eligibility(total_matches=306, matches_with_cutoff_odds=244)

    assert result.coverage == pytest.approx(244 / 306)
    assert result.eligible is False
