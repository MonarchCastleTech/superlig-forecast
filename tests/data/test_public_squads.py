from datetime import UTC, datetime

import orjson

from superlig_forecast.data.fetch import FetchResult
from superlig_forecast.data.public_squads import (
    DATASET_CLUBS_FILE_URL,
    DATASET_INFO_URL,
    DATASET_PLAYERS_FILE_URL,
    fetch_public_squad_snapshot,
    parse_public_squads,
)


def player_csv(clubs: int = 2) -> bytes:
    header = (
        "player_id,current_club_id,current_club_name,market_value_in_eur,"
        "current_club_domestic_competition_id\n"
    )
    rows = [
        f"{club * 100 + player},{club},Club {club},{1_000_000 + player},TR1"
        for club in range(1, clubs + 1)
        for player in range(1, 12)
    ]
    rows.append("999,99,Foreign Club,9000000,GB1")
    return (header + "\n".join(rows) + "\n").encode()


def club_csv(clubs: int = 2) -> bytes:
    header = "club_id,name,domestic_competition_id,last_season\n"
    rows = [f"{club},Club {club},TR1,2026" for club in range(1, clubs + 1)]
    rows.extend(["90,Old Club,TR1,2025", "99,Foreign Club,GB1,2026"])
    return (header + "\n".join(rows) + "\n").encode()


def test_parse_public_squads_aggregates_only_tr1() -> None:
    rows = parse_public_squads(player_csv(), club_csv(), expected_clubs=2)
    assert [row.club_name for row in rows] == ["Club 1", "Club 2"]
    assert all(row.squad_size == 11 for row in rows)
    assert rows[0].squad_value_eur == 11_000_066


def test_parse_public_squads_rejects_incomplete_league() -> None:
    try:
        parse_public_squads(player_csv(), club_csv(), expected_clubs=18)
    except ValueError as error:
        assert "covered 2 current clubs; expected 18" in str(error)
    else:
        raise AssertionError("incomplete public league was accepted")


class FakeFetcher:
    def fetch(self, request):  # type: ignore[no-untyped-def]
        if request.url == DATASET_INFO_URL:
            content = orjson.dumps(
                {
                    "isPrivate": False,
                    "currentVersionNumber": 700,
                    "lastUpdated": "2026-08-29T12:00:00Z",
                    "licenseName": "CC0: Public Domain",
                }
            )
        elif request.url == f"{DATASET_PLAYERS_FILE_URL}?datasetVersionNumber=700":
            content = player_csv(18)
        else:
            assert request.url == f"{DATASET_CLUBS_FILE_URL}?datasetVersionNumber=700"
            content = club_csv(18)
        return FetchResult(
            source=request.source,
            url=request.url,
            fetched_at=datetime(2026, 8, 30, tzinfo=UTC),
            status_code=200,
            content_type="application/octet-stream",
            content=content,
            extension=request.extension,
        )


def test_fetch_public_squad_snapshot_pins_latest_public_version() -> None:
    snapshot = fetch_public_squad_snapshot(FakeFetcher())  # type: ignore[arg-type]
    assert snapshot.version == 700
    assert snapshot.snapshot_at == datetime(2026, 8, 29, 12, tzinfo=UTC)
    assert len(snapshot.squads) == 18
