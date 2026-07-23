from datetime import UTC, datetime
from pathlib import Path

from superlig_forecast.data.fetch import FetchResult
from superlig_forecast.data.snapshots import SnapshotStore


def successful_result(content: bytes = b"same bytes") -> FetchResult:
    return FetchResult(
        source="tff",
        url="https://www.tff.org/default.aspx?pageID=86",
        fetched_at=datetime(2026, 7, 23, tzinfo=UTC),
        status_code=200,
        content_type="text/html",
        content=content,
        extension=".html",
    )


def test_same_payload_is_content_addressed_once(tmp_path: Path) -> None:
    store = SnapshotStore(tmp_path)

    first = store.put(successful_result())
    second = store.put(successful_result())

    assert first.sha256 == second.sha256
    assert first.payload_path == second.payload_path
    assert first.payload_path.read_bytes() == b"same bytes"
    assert len(list((tmp_path / "tff").glob("*.html"))) == 1


def test_failed_fetch_does_not_replace_latest(tmp_path: Path) -> None:
    store = SnapshotStore(tmp_path)
    saved = store.put(successful_result())

    store.record_failure(
        source="tff",
        url="https://www.tff.org/default.aspx?pageID=86",
        reason="503",
        failed_at=datetime(2026, 7, 23, 1, tzinfo=UTC),
    )

    assert store.latest("tff") == saved
