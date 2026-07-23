# Süper Lig Forecast

A reproducible, point-in-time forecasting engine for Turkish football matches and Süper Lig championship probabilities.

## Development

```powershell
uv sync
uv run pytest
uv run ruff check src tests
uv run mypy src
```

The interactive dashboard is intentionally deferred. Engine outputs will be exported as Parquet and JSON.

## Reproducible runbook

```powershell
uv run superlig fetch-data --source tff --season 2026-27 --dry-run
uv run superlig build-snapshots --output data/model.duckdb
uv run superlig train-model --output artifacts/model.json
uv run superlig backtest --output artifacts/backtest.json
uv run superlig forecast-season --demo --simulations 5000000 --seed 202627 --output artifacts/forecast
uv run superlig export-results --output artifacts/report
```

The `--demo` forecast validates the full simulation/export path. A production forecast must use normalized real fixtures, point-in-time player features, and trained artifacts; the CLI refuses to label a demo run as production.
