import json
from pathlib import Path

import pytest

from superlig_forecast.data.sportsdb import parse_sportsdb_events

FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_parses_turkish_names_null_scores_and_statuses() -> None:
    batch = parse_sportsdb_events(
        (FIXTURES / "sportsdb_events.json").read_bytes()
    )
    assert batch.competition == "TSL"
    assert batch.matches[0].away_team == "Fenerbahçe A.Ş."
    assert batch.matches[1].home_score is None
    assert [match.status for match in batch.matches] == [
        "finished",
        "scheduled",
        "postponed",
    ]


def test_rejects_event_from_wrong_league() -> None:
    payload = json.loads(
        (FIXTURES / "sportsdb_events.json").read_text(encoding="utf-8")
    )
    payload["events"][0]["strLeague"] = "Premier League"
    with pytest.raises(ValueError, match="wrong competition"):
        parse_sportsdb_events(json.dumps(payload).encode())
