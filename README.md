# Süper Lig Forecast

A reproducible, point-in-time forecasting engine for Turkish football matches and
Süper Lig championship probabilities. It is a forecast-quality research project,
not a betting system.

The engine combines:

- official TFF current competition/fixture snapshots for the Süper Lig, 1. Lig,
  2. Lig, 3. Lig, and Turkish Cup;
- 10,000+ normalized Turkish top-flight matches;
- 50,149 historical players, 507,815 valuation observations, 1.89M appearances,
  and 3.18M lineup rows;
- 560 live 2026-27 players and all 18 current squad totals;
- a recency-weighted Dixon-Coles structural model;
- de-vigged bookmaker consensus where point-in-time odds exist;
- conservative current-squad market-value adjustments; and
- deterministic, chunked Monte Carlo season simulation.

## Development

```powershell
uv sync
uv run pytest
uv run ruff check src tests
uv run mypy src

cd dashboard
npm ci
npm test
npm run lint
```

Engine outputs are JSON, CSV, Parquet, and PNG files. The interactive dashboard
uses a versioned static JSON export so it remains independent of DuckDB and the
raw source snapshots at runtime.

## Reproducible runbook

```powershell
uv run superlig fetch-data --source transfermarkt --season 2026-27 --output data/raw
uv run superlig fetch-data --source historical-results --season 2026-27 --output data/raw
uv run superlig fetch-data --source odds --season 2026-27 --output data/raw
uv run superlig fetch-data --source tff --season 2026-27 --output data/raw
uv run superlig fetch-data --source transfermarkt-current --season 2026-27 --output data/raw

uv run superlig build-snapshots `
  --transfermarkt-archive <transfermarkt-snapshot.zip> `
  --historical-results-archive <historical-results-snapshot.zip> `
  --odds-archive <oddsportal-snapshot.zip> `
  --output data/model.duckdb

uv run superlig fetch-current-squads `
  --league-page <current-transfermarkt-league.html> `
  --season 2026 --output data/raw

uv run superlig build-current-players `
  --league-page <current-transfermarkt-league.html> `
  --raw-dir data/raw --warehouse data/model.duckdb `
  --output data/processed/current-players-2026.parquet

uv run superlig train-model `
  --warehouse data/model.duckdb --before-season 2026 `
  --squad-page <current-transfermarkt-league.html> `
  --output artifacts/model-2026-27.json

uv run superlig backtest `
  --warehouse data/model.duckdb --start-season 2006 --end-season 2025 `
  --market-weight 0.9 --output artifacts/backtest-20-seasons.json

uv run superlig backtest-positions `
  --warehouse data/model.duckdb --start-season 2006 --end-season 2025 `
  --simulations 20000 --seed 202627 `
  --output artifacts/backtest-positions-20-seasons.json

uv run superlig forecast-season `
  --warehouse data/model.duckdb `
  --squad-page <current-transfermarkt-league.html> `
  --tff-page <current-tff-super-lig.html> `
  --season 2026 --simulations 5000000 --seed 202627 `
  --output artifacts/forecast-2026-27-5m

uv run superlig export-results --output artifacts/report
```

Use `forecast-season --demo` only for a four-team smoke test.

## Interactive dashboard

Refresh the dashboard data after a new forecast or backtest:

```powershell
uv run superlig export-dashboard-data `
  --forecast artifacts/forecast-2026-27-5m `
  --backtest artifacts/backtest-20-seasons.json `
  --position-backtest artifacts/backtest-positions-20-seasons.json `
  --output dashboard/public/data/dashboard.json
```

Run the local dashboard:

```powershell
.\run-dashboard.ps1
```

Open `http://localhost:3000`.

- Enter any positive whole-number target and press **Play** for a finite run.
  The worker stops exactly at the requested season count.
- Enable **Run until stopped** for an open-ended run. **Pause** preserves all
  cumulative counts, **Resume** continues the same run, and **Stop** ends it.
- Choose any exact finishing position from 1st through 18th. The live graph and
  possible table update as yielded simulation batches arrive.
- Reuse the same seed and inputs to reproduce a run, or press **New seed** to
  explore another deterministic sequence.
- **Live** results are computed in your browser from the published fixture xG.
  **Published reference** results are the checked-in five-million-season audit
  artifact and do not change while you play.

The dashboard also includes all fixture forecasts, full club-by-position
probabilities, the 20-season table and match backtests, and methodology notes.

## Verified backtest

The checked-in engine contract uses 20 strict expanding-window test folds:
2006-07 through 2025-26. Training rows always predate the test season. Proper
scores include multiclass log loss and Brier score for naïve, structural,
market-only, and hybrid forecasts. The generated acceptance section is the
machine-readable quality gate. A separate table backtest simulates every target
season and scores the probability assigned to every club's actual finishing
position, expected-rank error, and rank correlation against uniform baselines.

## Known modeling boundary

The current preseason forecast generates a balanced 306-match double round
robin from the 18 official clubs. Points, goal difference, and goals scored are
simulated exactly; head-to-head is presently approximated by the later
tie-breakers. See [TODO.md](TODO.md) for the remaining research work.
