import json
from pathlib import Path

import pytest

from superlig_forecast.data.football_data_org import (
    parse_football_data_matches,
)
from superlig_forecast.data.structured_sources import (
    ProviderBatch,
    StructuredMatch,
    select_match_source,
)

FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_parses_finished_scheduled_and_postponed_matches() -> None:
    batch = parse_football_data_matches((FIXTURES / "football_data_matches.json").read_bytes())
    assert batch.competition == "TSL"
    assert [match.status for match in batch.matches] == [
        "finished",
        "scheduled",
        "postponed",
    ]
    assert batch.matches[0].home_team == "Galatasaray A.Ş."
    assert (batch.matches[0].home_score, batch.matches[0].away_score) == (2, 1)
    assert batch.matches[1].home_score is None


def test_rejects_wrong_competition() -> None:
    payload = json.loads((FIXTURES / "football_data_matches.json").read_text(encoding="utf-8"))
    payload["competition"]["code"] = "PL"
    with pytest.raises(ValueError, match="expected TSL"):
        parse_football_data_matches(json.dumps(payload).encode())


def test_selects_first_available_provider_reconciled_with_tff() -> None:
    match = StructuredMatch(
        "2026-08-14",
        "Galatasaray",
        "Fenerbahçe",
        2,
        1,
        "finished",
    )
    unavailable = ProviderBatch(
        "football-data.org",
        "TSL",
        "2026",
        "2026-07-25T10:00:00Z",
        (),
        available=False,
        reason="token missing",
    )
    sportsdb = ProviderBatch(
        "thesportsdb",
        "TSL",
        "2026",
        "2026-07-25T10:00:00Z",
        (match,),
    )
    tff = ProviderBatch(
        "tff",
        "TSL",
        "2026",
        "2026-07-25T10:00:00Z",
        (match,),
    )
    assert select_match_source(unavailable, sportsdb, tff) is sportsdb
