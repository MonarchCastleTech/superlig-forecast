"""football-data.org v4 adapter for Süper Lig fixtures and results."""

from __future__ import annotations

import json
import os
from typing import Any, cast

import httpx

from superlig_forecast.data.structured_sources import (
    ProviderBatch,
    StructuredMatch,
)

API_URL = "https://api.football-data.org/v4/competitions/TSL/matches"
STATUS_MAP = {
    "FINISHED": "finished",
    "POSTPONED": "postponed",
    "CANCELLED": "cancelled",
}


def _mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"football-data.org {label} must be an object")
    return cast(dict[str, Any], value)


def parse_football_data_matches(payload: bytes) -> ProviderBatch:
    root = _mapping(json.loads(payload), "payload")
    competition = _mapping(root.get("competition"), "competition")
    if competition.get("code") != "TSL":
        raise ValueError(
            f"expected TSL competition, received {competition.get('code')!r}"
        )
    filters = _mapping(root.get("filters", {}), "filters")
    result_set = _mapping(root.get("resultSet", {}), "resultSet")
    raw_matches = root.get("matches")
    if not isinstance(raw_matches, list):
        raise ValueError("football-data.org matches must be a list")

    matches: list[StructuredMatch] = []
    for raw in raw_matches:
        item = _mapping(raw, "match")
        home = _mapping(item.get("homeTeam"), "home team")
        away = _mapping(item.get("awayTeam"), "away team")
        score = _mapping(item.get("score", {}), "score")
        full_time = _mapping(score.get("fullTime", {}), "full-time score")
        raw_status = str(item.get("status", "SCHEDULED")).upper()
        status = STATUS_MAP.get(raw_status, "scheduled")
        home_score = full_time.get("home")
        away_score = full_time.get("away")
        matches.append(
            StructuredMatch(
                played_on=str(item["utcDate"])[:10],
                home_team=str(home["name"]),
                away_team=str(away["name"]),
                home_score=int(home_score) if home_score is not None else None,
                away_score=int(away_score) if away_score is not None else None,
                status=cast(Any, status),
                provider_id=str(item["id"]),
            )
        )

    return ProviderBatch(
        provider="football-data.org",
        competition="TSL",
        season=str(filters.get("season", "")),
        fetched_at=str(result_set.get("lastUpdated", "")),
        matches=tuple(matches),
    )


def fetch_football_data_matches(
    season: str,
    *,
    token: str | None = None,
) -> ProviderBatch:
    api_token = token or os.getenv("FOOTBALL_DATA_API_TOKEN")
    if not api_token:
        return ProviderBatch(
            "football-data.org",
            "TSL",
            season,
            "",
            (),
            available=False,
            reason="FOOTBALL_DATA_API_TOKEN is not configured",
        )
    response = httpx.get(
        API_URL,
        params={"season": season},
        headers={
            "X-Auth-Token": api_token,
            "User-Agent": "superlig-forecast-updater/1.0",
        },
        timeout=httpx.Timeout(60.0, connect=15.0),
    )
    if response.status_code in {400, 401, 403, 404}:
        return ProviderBatch(
            "football-data.org",
            "TSL",
            season,
            "",
            (),
            available=False,
            reason=f"TSL access denied with HTTP {response.status_code}",
        )
    response.raise_for_status()
    return parse_football_data_matches(response.content)
