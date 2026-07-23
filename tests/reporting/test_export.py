from pathlib import Path

import polars as pl

from superlig_forecast.reporting.export import TIMELINE_COLUMNS, export_timeline
from superlig_forecast.reporting.charts import (
    backtest_log_loss_chart,
    championship_convergence,
)


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


def test_forecast_and_backtest_charts_are_written(tmp_path: Path) -> None:
    convergence = pl.DataFrame(
        {
            "simulation_count": [100, 1000, 100, 1000],
            "club_id": ["A", "A", "B", "B"],
            "champion_probability": [0.6, 0.58, 0.4, 0.42],
        }
    )
    backtest = pl.DataFrame(
        {
            "season": [2024, 2025],
            "naive_log_loss": [1.08, 1.07],
            "structural_log_loss": [1.03, 1.02],
            "hybrid_log_loss": [1.00, 0.99],
            "market_log_loss": [1.01, None],
        }
    )

    forecast_path = championship_convergence(convergence, tmp_path / "convergence.png")
    backtest_path = backtest_log_loss_chart(backtest, tmp_path / "backtest.png")

    assert forecast_path.stat().st_size > 0
    assert backtest_path.stat().st_size > 0
