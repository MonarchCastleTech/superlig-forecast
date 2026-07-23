"""Parquet and JSON export contracts."""

from pathlib import Path

import polars as pl

TIMELINE_COLUMNS = [
    "snapshot_id",
    "observed_at",
    "season",
    "club_id",
    "champion_probability",
    "delta_probability",
    "result_delta",
    "squad_delta",
    "lineup_delta",
    "market_delta",
    "interaction_delta",
    "model_version",
    "data_hash",
]


def export_timeline(frame: pl.DataFrame, output_dir: Path) -> Path:
    missing = set(TIMELINE_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"timeline export missing columns: {sorted(missing)}")
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "championship_timeline.parquet"
    frame.select(TIMELINE_COLUMNS).write_parquet(path, compression="zstd")
    return path
