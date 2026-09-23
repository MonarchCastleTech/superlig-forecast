# Süper Lig Forecast

A transparent forecast of the 2026–27 Turkish Süper Lig from
[Monarch Castle Technologies](https://monarchcastletech.github.io).

**Public dashboard:** <https://monarchcastletech.github.io/superlig-forecast/>

> This is a forecast-quality research project, not a betting website or betting
> advice. Probabilities are estimates, not guarantees. They can be wrong and
> will change as new official match results become available.

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
five-million-season result and is refreshed by GitHub Actions every
six hours.

**Full methodology:** <https://monarchcastletech.github.io/superlig-forecast/methodology/>

**Publication recovery (24 September 2026):** The earlier candidate missed completed fixtures and used a squad-value source that included three clubs from the previous season. The scheduled pipeline now fetches all 34 official TFF fixture weeks and derives the 18 current clubs from TFF. It uses the historically evaluated structural match model with the unvalidated squad-value adjustment disabled. It publishes only when the official source includes all clubs, completed results and a latest match date. If the source fails, the existing withdrawal notice remains.

The withdrawn pre-recovery payload is retained solely as `dashboard/tests/fixtures/withdrawn-dashboard.json` for renderer checks; its numerical outputs are **not publishable current forecasts**. The scheduled refresh replaces the public withdrawal file only after the publication gate passes.

## Methodology

### Forecast target

The match model estimates home-win, draw, and away-win probabilities. The
season model estimates distributions over final positions, points, goal
difference, and championship outcomes. It does not attempt to predict an exact
score.

### Data and temporal integrity

The live forecast consumes all 34 official TFF fixture weeks, fixes completed
scores into the current table and identifies the 18 clubs from the same official
source. Raw pages are content-addressed during each run. Historical evaluation
is temporal: each test season is fitted using only earlier match results. No
current squad value is imputed, and the public data marks squad values null.

### Structural and market information

A recency-weighted scoring-ratio model estimates separate home/away attack and
defence factors with shrinkage toward league means. A fixed Dixon–Coles
correction modifies the four low-score cells. Historical odds are used only in
backtest comparison baselines, not in the live title forecast. Current aggregate
squad value adjustment is disabled in the current official-results-only mode;
the earlier 0.10 adjustment was not validated inside the checked-in folds.

### Current-season state

Completed official scores are fixed into the starting table. Every other ordered
home-and-away pairing is sampled. Scheduled updates fetch each TFF week, rebuild
the current state, and publish only after validation succeeds. Fixtures without
an assigned kickoff remain in the raw official pages but do not enter the dated
match feed. Stale or incomplete input blocks publication.

### Monte Carlo

Five million season paths sample every remaining match from its calibrated
outcome/score distribution. Each path applies points, goal difference, and goals
scored to create one possible table. Checkpoints reveal how the title
probabilities stabilize as the number of paths grows. The recorded seed makes
the simulation repeatable only with the same code, dependencies, model artifact,
and exact raw TFF pages.

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
The match and table backtests omit the current squad-value adjustment. Historical
odds affect only the market and blended comparison series. These results validate
the historical scoring-ratio core and simulation structure, not the complete
live forecast or its 0.10 value coefficient.

### Limitations

Market values are imperfect proxies for player quality and availability.
Injuries, tactical changes, discipline, financial events, and late transfers may
not be represented immediately. Exact TFF head-to-head mini-table tie-breaking
is not implemented; unresolved ties use stable internal team order. Monte Carlo confidence
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

`.github/workflows/update-forecast.yml` runs the six-hourly stateless data refresh and
commits a new validated publication when inputs changed. It restores compact
trained-model and backtest seeds from `automation/seeds/`, fetches current TFF
competition pages plus the squad-value sources, applies completed scores,
reruns the five-million-path season forecast, and atomically promotes the
dashboard JSON only after freshness and reconciliation checks pass.

Market data is live-first. If Transfermarkt returns an incomplete page to a
GitHub-hosted runner, automation first retrieves the league overview through
Jina Reader's anonymous HTML endpoint and validates all 18 aggregate squad
totals. If that route also fails, it downloads only the current `clubs.csv` and
`players.csv` files from the anonymous CC0 dataset endpoint, pins its version,
reconstructs all 18 squad totals, and preserves the dataset timestamp.
If that fallback is too old or incomplete, publication fails and the dead-man
workflow opens or updates a GitHub issue. Transfers and valuation changes are
published only after a complete direct squad-page fetch.

`.github/workflows/deploy-pages.yml` tests and exports the Vite dashboard,
then deploys the static artifact to GitHub Pages. An optional
`FOOTBALL_DATA_API_TOKEN` repository secret can enable the configured API path;
the updater retains its documented free-source fallbacks. TheSportsDB v1 uses
its documented public key (`123`) and requires no account; TFF remains the
official verification source.

Each remaining fixture carries a presentation-only `Predicted: Yes/No` flag.
The flag does not alter any probability or simulation. The scheduled workflow
generates the next fixture forecasts with the Python engine and free-source
fallbacks; no Codex, ChatGPT sign-in, or manual entry is required. Older
dashboard snapshots default existing forecast rows to `Yes` for compatibility.

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
