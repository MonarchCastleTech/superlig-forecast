from datetime import UTC, datetime
from pathlib import Path

import pytest

from superlig_forecast.data.odds import OddsAdapter

CSV = Path(__file__).parents[1] / "fixtures" / "odds" / "turkey_odds.csv"


def test_wide_provider_columns_become_timestamped_rows() -> None:
    rows = OddsAdapter().read(CSV, observed_at=datetime(2021, 8, 12, tzinfo=UTC))

    assert set(rows["provider"]) == {"Bet365", "Pinnacle", "Average"}
    assert rows.filter(rows["provider"] == "Bet365")["home_odds"].item() == 1.72


def test_missing_observation_time_is_rejected() -> None:
    with pytest.raises(ValueError, match="observation timestamp"):
        OddsAdapter().read(CSV, observed_at=None)
