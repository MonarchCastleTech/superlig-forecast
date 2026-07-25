from datetime import UTC, datetime
from pathlib import Path

from superlig_forecast.data.tff import TffAdapter

FIXTURES = Path(__file__).parents[1] / "fixtures" / "tff"


def test_discovers_all_required_tff_pages() -> None:
    html = (FIXTURES / "leagues.html").read_text(encoding="utf-8")

    found = TffAdapter().parse_competitions(html)

    assert {(item.page_id, item.tier) for item in found} == {
        (198, 1),
        (142, 2),
        (976, 3),
        (971, 4),
        (288, 0),
    }


def test_parses_match_id_clubs_kickoff_and_unplayed_score() -> None:
    html = (FIXTURES / "super_lig_fixture.html").read_text(encoding="utf-8")

    matches = TffAdapter().parse_matches(
        html,
        observed_at=datetime(2026, 7, 23, tzinfo=UTC),
        competition_id="TR1",
        season="2026-27",
    )
    match = next(item for item in matches if item.match_id == "tff:317790")

    assert match.home_club_id == "tff-club:3604"
    assert match.away_club_id == "tff-club:3199"
    assert match.home_club_name == "Galatasaray A.Ş."
    assert match.away_club_name == "Çorum FK"
    assert match.kickoff.isoformat() == "2026-08-14T21:30:00+03:00"
    assert match.is_finished is False


def test_parses_finished_score() -> None:
    html = (FIXTURES / "super_lig_fixture.html").read_text(encoding="utf-8")

    matches = TffAdapter().parse_matches(
        html,
        observed_at=datetime(2026, 7, 23, tzinfo=UTC),
        competition_id="TR1",
        season="2026-27",
    )
    match = next(item for item in matches if item.match_id == "tff:317785")

    assert (match.home_goals, match.away_goals) == (2, 1)


def test_exposes_normalized_structured_matches() -> None:
    page = (FIXTURES / "super_lig_fixture.html").read_bytes()
    batch = TffAdapter().structured_matches(
        page,
        season="2026-27",
        declared_charset="utf-8",
    )
    finished = next(
        item for item in batch.matches if item.provider_id == "tff:317785"
    )
    scheduled = next(
        item for item in batch.matches if item.provider_id == "tff:317790"
    )
    assert batch.competition == "TSL"
    assert finished.status == "finished"
    assert scheduled.status == "scheduled"
