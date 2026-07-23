from pathlib import Path

import polars as pl

from superlig_forecast.reporting.export import TIMELINE_COLUMNS, export_timeline


def test_timeline_export_has_stable_contract(tmp_path: Path) -> None:
    frame = pl.DataFrame({column: [0.0] for column in TIMELINE_COLUMNS}).with_columns(
        pl.lit("s1").alias("snapshot_id"),
        pl.lit("2026-07-23").alias("observed_at"),
        pl.lit("2026-27").alias("season"),
        pl.lit("club:1").alias("club_id"),
        pl.lit("v1").alias("model_version"),
        pl.lit("hash").alias("data_hash"),
    )
    path = export_timeline(frame, tmp_path)
    assert pl.read_parquet(path).columns == TIMELINE_COLUMNS
