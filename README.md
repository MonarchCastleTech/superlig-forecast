# Süper Lig Forecast

An open, reproducible forecast of the 2026–27 Turkish Süper Lig from
[Monarch Castle Technologies](https://monarchcastle.tech).

**Public dashboard:** <https://monarchcastletech.github.io/superlig-forecast/>

> This is a forecast-quality research project, not a betting website or betting
> advice. Probabilities are estimates, not guarantees. They can be wrong and
> will change as new matches, transfers, and market values become available.

## What the dashboard publishes

- title probabilities and their Monte Carlo convergence;
- a complete possible final table with expected points and average rank;
- probabilities for every club finishing in every position;
- relegation, top-four, and exact-position probabilities;
- home-win, draw, and away-win probabilities for remaining matches;
- the most likely match outcome, without exact-score predictions;
- a strict 20-season expanding-window backtest; and
- the publication time and current data-alignment audit.

The public site has no simulation controls. It presents the latest checked,
reproducible five-million-season result and is refreshed by GitHub Actions once
per day.

## Methodology

### Forecast target

The match model estimates home-win, draw, and away-win probabilities. The
season model estimates distributions over final positions, points, goal
difference, and championship outcomes. It does not attempt to predict an exact
score.

### Data and temporal integrity

The pipeline normalizes point-in-time match results, fixtures, player and squad
market values, lineups, and available pre-match odds. Historical evaluation is
strictly temporal: each test season is predicted using only earlier data.
Promoted teams enter through their lower-division history and a partial-pooling
adjustment, so the league's changing membership is represented in every fold.

### Structural and market information

A recency-weighted Dixon–Coles model estimates attack, defence, home advantage,
and low-score dependence. When point-in-time odds exist, de-vigged market
probabilities are blended with the structural estimate. Current squad market
value contributes a conservative strength adjustment selected within historical
folds rather than on the forecast season.

### Current-season state

Completed official scores are fixed into the starting table. Only remaining
fixtures are sampled. Scheduled updates fetch new match results, transfers, and
market values, reconcile club identities, rebuild the current state, and publish
only after validation succeeds.

### Monte Carlo

Five million season paths sample every remaining match from its calibrated
outcome/score distribution. Each path applies points, goal difference, and goals
scored to create one possible table. Checkpoints reveal how the title
probabilities stabilize as the number of paths grows, and the recorded seed
makes the reference publication repeatable.

### Backtesting

The checked-in model contract uses 20 expanding-window folds, 2006–07 through
2025–26. Training rows always predate the test season. Match forecasts are
compared with naive, structural, market-only, and hybrid baselines using:

- **log loss**, which penalizes confident probability forecasts that disagree
  with the outcome; and
- **Brier score**, the squared distance between forecast probabilities and the
  observed outcome.

Lower is better for both. A separate table backtest simulates each historical
season and scores the probability assigned to every club's actual finishing
position, expected-rank error, and rank correlation against uniform baselines.
Passing a backtest is evidence of historical forecast quality, not proof of
future accuracy.

### Limitations

Market values are imperfect proxies for player quality and availability.
Injuries, tactical changes, discipline, financial events, and late transfers may
not be represented immediately. Exact TFF head-to-head mini-table tie-breaking
is currently approximated by later table criteria. Monte Carlo confidence
intervals measure simulation noise conditional on the model; they do not capture
all model or data uncertainty.

## Run locally

Requirements: Python managed by `uv`, Node.js, and npm.

```powershell
uv sync
uv run pytest

cd dashboard
npm ci
npm test
npm run dev
```

Open <http://localhost:3000>.

The convenience launcher from the repository root is:

```powershell
.\run-dashboard.ps1
```

## Reproduce the research pipeline

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

uv run superlig export-dashboard-data `
  --forecast artifacts/forecast-2026-27-5m `
  --backtest artifacts/backtest-20-seasons.json `
  --position-backtest artifacts/backtest-positions-20-seasons.json `
  --output dashboard/public/data/dashboard.json
```

Use `forecast-season --demo` only for a four-team smoke test.

## Automated publication

`.github/workflows/update-forecast.yml` runs the stateless data refresh and
commits a new validated publication when inputs changed. It restores compact
trained-model and backtest seeds from `automation/seeds/`, fetches current TFF
competition pages plus the squad-value sources, applies completed scores,
reruns the five-million-path season forecast, and atomically promotes the
dashboard JSON only after freshness and reconciliation checks pass.

Market data is live-first. If Transfermarkt returns an incomplete page to a
GitHub-hosted runner, the match feed still refreshes and the forecast uses the
dated `current_squads` snapshot embedded in
`automation/seeds/model-2026-27.json`. The dashboard records that snapshot's
true timestamp and fallback note; it never relabels old values as newly fetched.
Transfers and valuation changes are published only after a complete live squad
fetch.

`.github/workflows/deploy-pages.yml` tests and exports the Next.js dashboard,
then deploys the static artifact to GitHub Pages. An optional
`FOOTBALL_DATA_API_TOKEN` repository secret can enable the configured API path;
the updater retains its documented free-source fallbacks.

## Development verification

```powershell
uv run pytest
uv run ruff check src tests
uv run mypy src

cd dashboard
npm ci
npm test
npm run typecheck
npm run lint
```

See [TODO.md](TODO.md) for open research and data-quality work.
