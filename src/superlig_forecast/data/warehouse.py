"""Canonical DuckDB schema and deterministic build manifests."""

import hashlib
from pathlib import Path
from typing import Any

import duckdb
import orjson
from pydantic import BaseModel, ConfigDict

WAREHOUSE_TABLES = (
    "competitions",
    "clubs",
    "club_aliases",
    "players",
    "player_aliases",
    "matches",
    "lineups",
    "appearances",
    "valuations",
    "transfers",
    "odds",
    "raw_manifests",
    "coverage",
)


class BuildManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    data_hash: str
    table_count: int


class Warehouse:
    """Creates the stable analytical schema."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def build(self, snapshot_manifests: list[Any]) -> BuildManifest:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(self.path)) as connection:
            for table in WAREHOUSE_TABLES:
                connection.execute(f"create table if not exists {table}(record_id varchar)")
        payload = orjson.dumps(snapshot_manifests, option=orjson.OPT_SORT_KEYS, default=str)
        return BuildManifest(
            data_hash=hashlib.sha256(payload).hexdigest(),
            table_count=len(WAREHOUSE_TABLES),
        )

    def tables(self) -> list[str]:
        with duckdb.connect(str(self.path), read_only=True) as connection:
            return [row[0] for row in connection.execute("show tables").fetchall()]
