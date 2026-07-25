from datetime import UTC, datetime
import json
from pathlib import Path

import pytest

from superlig_forecast.data.structured_sources import (
    ProviderBatch,
    StructuredMatch,
)
from superlig_forecast.refresh import (
    RefreshBlocked,
    RefreshConfig,
    RefreshSources,
    refresh_forecast,
)


def sources(score: tuple[int, int] = (2, 1)) -> RefreshSources:
    primary = StructuredMatch(
        "2026-08-14",
        "Galatasaray",
        "Fenerbahçe",
        score[0],
        score[1],
        "finished",
    )
    official = StructuredMatch(
        "2026-08-14",
        "Galatasaray A.Ş.",
        "Fenerbahçe A.Ş.",
        2,
        1,
        "finished",
    )
    observed = datetime(2026, 8, 14, 22, tzinfo=UTC)
    return RefreshSources(
        candidate_payload={"schema_version": 1, "value": "same"},
        primary_matches=ProviderBatch("api", "TSL", "2026-27", observed.isoformat(), (primary,)),
        verification_matches=ProviderBatch(
            "tff", "TSL", "2026-27", observed.isoformat(), (official,)
        ),
        match_snapshot_at=observed,
        squad_snapshot_at=observed,
        valuation_snapshot_at=observed,
        latest_match_date="2026-08-14",
    )


def test_refresh_no_change_preserves_original_bytes(tmp_path: Path) -> None:
    output = tmp_path / "dashboard.json"
    current = sources()
    payload = {
        **current.candidate_payload,
        "freshness": {
            "generated_at": "2026-08-14T22:00:00+00:00",
            "match_snapshot_at": "2026-08-14T22:00:00+00:00",
            "squad_snapshot_at": "2026-08-14T22:00:00+00:00",
            "valuation_snapshot_at": "2026-08-14T22:00:00+00:00",
            "latest_match_date": "2026-08-14",
            "source_status": "fresh",
            "source_notes": [],
        },
    }
    original_output = json.dumps(payload, sort_keys=True).encode()
    output.write_bytes(original_output)
    config = RefreshConfig(
        season=2026,
        output=output,
        now=datetime(2026, 8, 14, 23, tzinfo=UTC),
    )

    result = refresh_forecast(config, sources=current)

    assert result.changed is False
    assert output.read_bytes() == original_output


def test_refresh_conflict_never_replaces_output(tmp_path: Path) -> None:
    output = tmp_path / "dashboard.json"
    original_output = b'{"schema_version":1,"sentinel":"keep"}'
    output.write_bytes(original_output)
    config = RefreshConfig(
        season=2026,
        output=output,
        now=datetime(2026, 8, 14, 23, tzinfo=UTC),
    )

    with pytest.raises(
        RefreshBlocked,
        match="match source reconciliation failed",
    ):
        refresh_forecast(config, sources=sources((1, 1)))

    assert output.read_bytes() == original_output
