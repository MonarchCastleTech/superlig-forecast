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

