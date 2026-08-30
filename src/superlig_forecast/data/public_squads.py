"""Keyless structured fallback for current Transfermarkt-derived squad values."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from io import StringIO

import orjson

from superlig_forecast.data.fetch import FetchRequest, Fetcher
from superlig_forecast.data.transfermarkt_live import CurrentSquadValue


DATASET_INFO_URL = "https://www.kaggle.com/api/v1/datasets/view/davidcariboo/player-scores"
DATASET_PLAYERS_FILE_URL = (
    "https://www.kaggle.com/api/v1/datasets/download/davidcariboo/player-scores/players.csv"
)
DATASET_CLUBS_FILE_URL = (
    "https://www.kaggle.com/api/v1/datasets/download/davidcariboo/player-scores/clubs.csv"
)


@dataclass(frozen=True, slots=True)
class PublicSquadSnapshot:
    """Validated top-flight squad totals plus immutable source provenance."""

    squads: tuple[CurrentSquadValue, ...]
    snapshot_at: datetime
    version: int
    source_url: str = DATASET_INFO_URL
    license_name: str = "CC0: Public Domain"

    def as_payload(self) -> dict[str, object]:
        return {
            "current_squads": [
                {
                    "club_id": row.club_id,
                    "club_name": row.club_name,
                    "squad_size": row.squad_size,
                    "squad_value_eur": row.squad_value_eur,
                }
                for row in self.squads
            ],
            "snapshot_at": self.snapshot_at.isoformat(),
            "source_url": self.source_url,
            "source_version": self.version,
            "license": self.license_name,
        }


def parse_public_squads(
    players_payload: bytes,
    clubs_payload: bytes,
    *,
    expected_clubs: int = 18,
) -> tuple[CurrentSquadValue, ...]:
    """Aggregate the public players table into one validated TR1 row per club."""

    try:
        players_text = players_payload.decode("utf-8-sig")
        clubs_text = clubs_payload.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError("public squad table is not valid UTF-8") from error
    top_flight_rows = [
        row
        for row in csv.DictReader(StringIO(clubs_text))
        if row.get("domestic_competition_id") == "TR1"
        and (row.get("last_season") or "").strip().isdigit()
    ]
    if not top_flight_rows:
        raise ValueError("public clubs table contains no TR1 season")
    current_season = max(int(row["last_season"]) for row in top_flight_rows)
    clubs = {
        int(row["club_id"]): (row.get("name") or "").strip()
        for row in top_flight_rows
        if int(row["last_season"]) == current_season
        and (row.get("club_id") or "").strip().isdigit()
    }
    if len(clubs) != expected_clubs or any(not name for name in clubs.values()):
        raise ValueError(
            f"public clubs table covered {len(clubs)} current clubs; expected {expected_clubs}"
        )
    totals: dict[int, tuple[str, int, int]] = {
        club_id: (name, 0, 0) for club_id, name in clubs.items()
    }
    for row in csv.DictReader(StringIO(players_text)):
        raw_id = (row.get("current_club_id") or "").strip()
        if not raw_id.isdigit() or int(raw_id) not in clubs:
            continue
        name = clubs[int(raw_id)]
        raw_value = (row.get("market_value_in_eur") or "").strip()
        try:
            value = int(float(raw_value)) if raw_value else 0
        except ValueError as error:
            raise ValueError(f"invalid market value for {name}") from error
        club_id = int(raw_id)
        existing = totals[club_id]
        totals[club_id] = (name, existing[1] + 1, existing[2] + value)
    squads = tuple(
        CurrentSquadValue(club_id, name, size, value)
        for club_id, (name, size, value) in sorted(totals.items())
    )
    invalid = [row.club_name for row in squads if row.squad_size < 11 or row.squad_value_eur <= 0]
    if invalid:
        raise ValueError(f"incomplete public squads: {', '.join(invalid)}")
    return squads


def fetch_public_squad_snapshot(
    fetcher: Fetcher | None = None,
) -> PublicSquadSnapshot:
    """Fetch latest anonymous public metadata and only the required players CSV."""

    client = fetcher or Fetcher()
    metadata = orjson.loads(
        client.fetch(FetchRequest(source="public-squad-metadata", url=DATASET_INFO_URL)).content
    )
    if not isinstance(metadata, dict) or metadata.get("isPrivate") is not False:
        raise ValueError("public squad dataset metadata is invalid or private")
    version = metadata.get("currentVersionNumber")
    updated = metadata.get("lastUpdated")
    license_name = metadata.get("licenseName")
    if not isinstance(version, int) or not isinstance(updated, str):
        raise ValueError("public squad dataset version metadata is incomplete")
    if not isinstance(license_name, str) or "CC0" not in license_name:
        raise ValueError("public squad dataset is not published under CC0")
    snapshot_at = datetime.fromisoformat(updated.replace("Z", "+00:00")).astimezone(UTC)
    players_url = f"{DATASET_PLAYERS_FILE_URL}?datasetVersionNumber={version}"
    clubs_url = f"{DATASET_CLUBS_FILE_URL}?datasetVersionNumber={version}"
    players = client.fetch(
        FetchRequest(
            source="public-squad-players",
            url=players_url,
            extension=".csv",
        )
    ).content
    clubs = client.fetch(
        FetchRequest(
            source="public-squad-clubs",
            url=clubs_url,
            extension=".csv",
        )
    ).content
    return PublicSquadSnapshot(
        squads=parse_public_squads(players, clubs),
        snapshot_at=snapshot_at,
        version=version,
        license_name=license_name,
    )
