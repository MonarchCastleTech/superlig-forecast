"""Atomic source-gated refresh of the static dashboard contract."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Mapping

import orjson

from superlig_forecast.data.structured_sources import (
    ProviderBatch,
    ReconciliationError,
    reconcile_matches,
    select_match_source,
)
from superlig_forecast.reporting.freshness import assess_freshness


class RefreshBlocked(RuntimeError):
    """Raised when candidate data cannot safely replace the current dashboard."""


@dataclass(frozen=True, slots=True)
class RefreshConfig:
    season: int
    simulations: int = 5_000_000
    seed: int = 202627
    output: Path = Path("dashboard/public/data/dashboard.json")
    now: datetime | None = None


@dataclass(frozen=True, slots=True)
class RefreshSources:
    candidate_payload: Mapping[str, Any]
    primary_matches: ProviderBatch
    verification_matches: ProviderBatch
    match_snapshot_at: datetime
    squad_snapshot_at: datetime
    valuation_snapshot_at: datetime
    latest_match_date: str | None
    source_notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RefreshResult:
    changed: bool
    output: Path
    selected_match_provider: str
    generated_at: str


def _without_generated_at(payload: object) -> object:
    if not isinstance(payload, dict):
        return payload
    clone = json.loads(json.dumps(payload))
    freshness = clone.get("freshness")
    if isinstance(freshness, dict):
        freshness["generated_at"] = ""
    clone.pop("publication_history", None)
    return clone


def _publication_snapshot(payload: object) -> dict[str, object] | None:
    if not isinstance(payload, dict):
        return None
    freshness = payload.get("freshness")
    championship = payload.get("championship")
    if not isinstance(freshness, dict) or not isinstance(championship, list):
        return None
    generated_at = freshness.get("generated_at")
    if not isinstance(generated_at, str):
        return None
    probabilities = {
        row["club"]: row["champion_probability"]
        for row in championship
        if isinstance(row, dict)
        and isinstance(row.get("club"), str)
        and isinstance(row.get("champion_probability"), (int, float))
    }
    return {"generated_at": generated_at, "probabilities": probabilities}


def _validate_candidate(payload: object) -> None:
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise RefreshBlocked("candidate dashboard schema is invalid")
    freshness = payload.get("freshness")
    if not isinstance(freshness, dict):
        raise RefreshBlocked("candidate dashboard freshness is missing")
    if freshness.get("source_status") != "fresh":
        raise RefreshBlocked("critical dashboard sources are stale or failed")


def _fallback_sources(config: RefreshConfig) -> RefreshSources:
    if not config.output.exists():
        raise RefreshBlocked("refresh requires an existing dashboard or explicit sources")
    modified = datetime.fromtimestamp(config.output.stat().st_mtime, tz=UTC)
    payload = orjson.loads(config.output.read_bytes())
    empty = ProviderBatch(
        "tff",
        "TSL",
        str(config.season),
        modified.isoformat(),
        (),
    )
    return RefreshSources(
        candidate_payload=payload,
        primary_matches=ProviderBatch(
            "none",
            "TSL",
            str(config.season),
            modified.isoformat(),
            (),
            available=False,
            reason="no explicit live source bundle",
        ),
        verification_matches=empty,
        match_snapshot_at=modified,
        squad_snapshot_at=modified,
        valuation_snapshot_at=modified,
        latest_match_date=None,
        source_notes=("Retained the latest validated local source bundle.",),
    )


def refresh_forecast(
    config: RefreshConfig,
    *,
    sources: RefreshSources | None = None,
) -> RefreshResult:
    active_sources = sources or _fallback_sources(config)
    try:
        report = reconcile_matches(
            active_sources.primary_matches,
            active_sources.verification_matches,
        )
        if report.conflicts:
            raise ReconciliationError("; ".join(report.conflicts))
        selected = select_match_source(
            active_sources.primary_matches,
            ProviderBatch(
                "thesportsdb",
                "TSL",
                str(config.season),
                "",
                (),
                available=False,
                reason="not supplied",
            ),
            active_sources.verification_matches,
        )
    except (ReconciliationError, ValueError) as error:
        raise RefreshBlocked(f"match source reconciliation failed: {error}") from error

    now = config.now or datetime.now(UTC)
    freshness = assess_freshness(
        now=now,
        match_snapshot_at=active_sources.match_snapshot_at,
        squad_snapshot_at=active_sources.squad_snapshot_at,
        valuation_snapshot_at=active_sources.valuation_snapshot_at,
        latest_match_date=active_sources.latest_match_date,
        notes=active_sources.source_notes,
    )
    candidate = json.loads(json.dumps(active_sources.candidate_payload))
    candidate["freshness"] = freshness.as_payload()
    _validate_candidate(candidate)

    existing: object | None = None
    if config.output.exists():
        try:
            existing = orjson.loads(config.output.read_bytes())
        except orjson.JSONDecodeError:
            existing = None
    has_history = isinstance(existing, dict) and isinstance(
        existing.get("publication_history"), list
    )
    if (has_history or _publication_snapshot(candidate) is None) and _without_generated_at(
        existing
    ) == _without_generated_at(candidate):
        return RefreshResult(
            changed=False,
            output=config.output,
            selected_match_provider=selected.provider,
            generated_at=freshness.generated_at,
        )

    history = list(existing.get("publication_history", [])) if isinstance(existing, dict) else []
    if not history:
        initial = _publication_snapshot(existing)
        if initial is not None:
            history.append(initial)
    latest = _publication_snapshot(candidate)
    if latest is not None and (
        not history or history[-1].get("generated_at") != latest["generated_at"]
    ):
        history.append(latest)
    candidate["publication_history"] = history[-730:]

    config.output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(
        prefix=".forecast-refresh-",
        dir=config.output.parent,
    ) as temporary_directory:
        staging = Path(temporary_directory)
        candidate_path = staging / "dashboard.json"
        candidate_path.write_bytes(
            orjson.dumps(
                candidate,
                option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
            )
        )
        staged_payload = orjson.loads(candidate_path.read_bytes())
        _validate_candidate(staged_payload)
        candidate_path.replace(config.output)

    return RefreshResult(
        changed=True,
        output=config.output,
        selected_match_provider=selected.provider,
        generated_at=freshness.generated_at,
    )
