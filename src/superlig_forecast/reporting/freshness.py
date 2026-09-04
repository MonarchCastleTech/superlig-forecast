"""Freshness assessment for dashboard source snapshots."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Literal

SourceStatus = Literal["fresh", "stale", "failed"]

MATCH_MAX_AGE = timedelta(hours=24)
SQUAD_MAX_AGE = timedelta(days=60)
VALUATION_MAX_AGE = timedelta(days=60)


@dataclass(frozen=True, slots=True)
class FreshnessReport:
    generated_at: str
    match_snapshot_at: str
    squad_snapshot_at: str
    valuation_snapshot_at: str
    latest_match_date: str | None
    source_status: SourceStatus
    source_notes: tuple[str, ...]

    def as_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload["source_notes"] = list(self.source_notes)
        return payload


def assess_freshness(
    *,
    now: datetime,
    match_snapshot_at: datetime,
    squad_snapshot_at: datetime,
    valuation_snapshot_at: datetime,
    latest_match_date: str | None,
    notes: tuple[str, ...] = (),
    failed: bool = False,
) -> FreshnessReport:
    ages = {
        "matches": (now - match_snapshot_at, MATCH_MAX_AGE),
        "squads": (now - squad_snapshot_at, SQUAD_MAX_AGE),
        "valuations": (now - valuation_snapshot_at, VALUATION_MAX_AGE),
    }
    stale = [
        f"{name} snapshot is older than {maximum}"
        for name, (age, maximum) in ages.items()
        if age < timedelta(0) or age > maximum
    ]
    status: SourceStatus = "failed" if failed else "stale" if stale else "fresh"
    return FreshnessReport(
        generated_at=now.isoformat(),
        match_snapshot_at=match_snapshot_at.isoformat(),
        squad_snapshot_at=squad_snapshot_at.isoformat(),
        valuation_snapshot_at=valuation_snapshot_at.isoformat(),
        latest_match_date=latest_match_date,
        source_status=status,
        source_notes=notes + tuple(stale),
    )
