"""TheSportsDB free-v1 adapter with a conservative rate limiter."""

from __future__ import annotations

import json
import threading
import time
from typing import Any, cast

import httpx

from superlig_forecast.data.identity import normalized_name
from superlig_forecast.data.structured_sources import (
    ProviderBatch,
    StructuredMatch,
)

API_URL = "https://www.thesportsdb.com/api/v1/json/123/eventsseason.php"
FREE_LEAGUE_ID = "4339"
ALLOWED_LEAGUES = {"super lig", "turkish super lig"}
_RATE_LOCK = threading.Lock()
_LAST_REQUEST_AT = 0.0


def _mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"TheSportsDB {label} must be an object")
    return cast(dict[str, Any], value)


def _status(value: object) -> str:
    normalized = normalized_name(str(value or ""))
    if "finish" in normalized:
        return "finished"
    if "postpon" in normalized:
        return "postponed"
    if "cancel" in normalized:
        return "cancelled"
    return "scheduled"


def _score(value: object) -> int | None:
    if value is None or value == "":
        return None
    return int(str(value))


def parse_sportsdb_events(payload: bytes) -> ProviderBatch:
    root = _mapping(json.loads(payload), "payload")
    raw_events = root.get("events")
    if raw_events is None:
        return ProviderBatch("thesportsdb", "TSL", "", "", ())
    if not isinstance(raw_events, list):
        raise ValueError("TheSportsDB events must be a list")

    matches: list[StructuredMatch] = []
    seasons: set[str] = set()
    for raw in raw_events:
        event = _mapping(raw, "event")
        league = normalized_name(str(event.get("strLeague", "")))
        if league not in ALLOWED_LEAGUES:
            raise ValueError(f"TheSportsDB event belongs to wrong competition {league!r}")
        season = str(event.get("strSeason", ""))
        seasons.add(season)
        status = _status(event.get("strStatus"))
        matches.append(
            StructuredMatch(
                played_on=str(event["dateEvent"]),
                home_team=str(event["strHomeTeam"]),
                away_team=str(event["strAwayTeam"]),
                home_score=_score(event.get("intHomeScore")),
                away_score=_score(event.get("intAwayScore")),
                status=cast(Any, status),
                provider_id=str(event["idEvent"]),
            )
        )
    if len(seasons) > 1:
        raise ValueError("TheSportsDB events contain multiple seasons")
    return ProviderBatch(
        provider="thesportsdb",
        competition="TSL",
        season=next(iter(seasons), ""),
        fetched_at="",
        matches=tuple(matches),
    )


def fetch_sportsdb_events(
    season: str,
    *,
    league_id: str = FREE_LEAGUE_ID,
) -> ProviderBatch:
    global _LAST_REQUEST_AT
    with _RATE_LOCK:
        wait_seconds = 2.0 - (time.monotonic() - _LAST_REQUEST_AT)
        if wait_seconds > 0:
            time.sleep(wait_seconds)
        response = httpx.get(
            API_URL,
            params={"id": league_id, "s": season},
            headers={"User-Agent": "superlig-forecast-updater/1.0"},
            timeout=httpx.Timeout(60.0, connect=15.0),
        )
        _LAST_REQUEST_AT = time.monotonic()
    if response.status_code in {400, 401, 403, 404, 429}:
        return ProviderBatch(
            "thesportsdb",
            "TSL",
            season,
            "",
            (),
            available=False,
            reason=f"free API unavailable with HTTP {response.status_code}",
        )
    response.raise_for_status()
    return parse_sportsdb_events(response.content)
