"""Immutable content-addressed raw snapshots."""

import hashlib
from datetime import datetime
from pathlib import Path

import orjson
from pydantic import BaseModel, ConfigDict

from superlig_forecast.data.fetch import FetchResult


class SnapshotManifest(BaseModel):
    """Metadata for one successful raw snapshot."""

    model_config = ConfigDict(frozen=True)

    source: str
    url: str
    fetched_at: datetime
    status_code: int
    content_type: str
    byte_count: int
    sha256: str
    payload_path: Path


class SnapshotStore:
    """Writes raw payloads once and appends audit manifests."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def put(self, result: FetchResult) -> SnapshotManifest:
        """Persist a successful payload by content hash."""

        digest = hashlib.sha256(result.content).hexdigest()
        payload_path = self.root / result.source / f"{digest}{result.extension}"
        payload_path.parent.mkdir(parents=True, exist_ok=True)
        if not payload_path.exists():
            temporary = payload_path.with_suffix(payload_path.suffix + ".partial")
            temporary.write_bytes(result.content)
            temporary.replace(payload_path)
        manifest = SnapshotManifest(
            source=result.source,
            url=result.url,
            fetched_at=result.fetched_at,
            status_code=result.status_code,
            content_type=result.content_type,
            byte_count=len(result.content),
            sha256=digest,
            payload_path=payload_path,
        )
        self._append_json(self._manifest_path(result.source), manifest.model_dump(mode="json"))
        return manifest

    def latest(self, source: str) -> SnapshotManifest | None:
        """Return the latest successful manifest for a source."""

        path = self._manifest_path(source)
        if not path.exists():
            return None
        lines = [line for line in path.read_bytes().splitlines() if line]
        if not lines:
            return None
        return SnapshotManifest.model_validate(orjson.loads(lines[-1]))

    def record_failure(
        self,
        *,
        source: str,
        url: str,
        reason: str,
        failed_at: datetime,
    ) -> None:
        """Append a failed acquisition without changing the latest success."""

        self._append_json(
            self.root / "_failures" / f"{source}.jsonl",
            {
                "source": source,
                "url": url,
                "reason": reason,
                "failed_at": failed_at.isoformat(),
            },
        )

    def _manifest_path(self, source: str) -> Path:
        return self.root / "_manifests" / f"{source}.jsonl"

    @staticmethod
    def _append_json(path: Path, payload: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("ab") as handle:
            handle.write(orjson.dumps(payload, option=orjson.OPT_APPEND_NEWLINE))

