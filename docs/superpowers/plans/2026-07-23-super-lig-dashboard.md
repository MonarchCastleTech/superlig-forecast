# Süper Lig Forecast Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and publish an interactive dashboard for the five-million-run
2026–27 forecast and twenty-season backtest.

**Architecture:** A tested Python adapter converts engine artifacts into a
single static JSON contract. A vinext/React site reads that contract and
provides client-side championship, convergence, fixture, and validation
interactions without coupling the frontend to DuckDB or raw data sources.

**Tech Stack:** Python 3.13, Typer, pytest, TypeScript, React, vinext, Vitest,
Recharts, CSS.

## Global Constraints

- Forecast quality only; no betting recommendations or stake language.
- Preserve the approved layered-hybrid layout.
- Use the complete 5,000,000-run forecast and 2006–2025 backtest artifacts.
- Missing data must remain missing rather than becoming zero.
- The hosted build must not require DuckDB or Python at runtime.
- Use deterministic, versioned static dashboard data.

---

### Task 1: Versioned dashboard export contract

**Files:**
- Create: `src/superlig_forecast/reporting/dashboard.py`
- Create: `tests/reporting/test_dashboard.py`
- Modify: `src/superlig_forecast/cli.py`

**Interfaces:**
- Consumes: forecast `manifest.json`, `champion-probabilities.csv`,
  `championship-convergence.csv`, `fixture-expectations.csv`, and backtest JSON.
- Produces: `build_dashboard_payload(forecast_dir: Path, backtest_path: Path) -> dict[str, Any]`
  and CLI command `superlig export-dashboard-data`.

- [ ] **Step 1: Write failing normalization tests**

Create fixture artifacts with two clubs, two checkpoints, one fixture, and one
backtest fold. Assert the output schema version, metadata, numeric probability
types, sorted clubs, checkpoints, fixtures, aggregate metrics, and folds.

- [ ] **Step 2: Verify the tests fail**

Run: `uv run pytest tests/reporting/test_dashboard.py -q`

Expected: FAIL because `superlig_forecast.reporting.dashboard` does not exist.

- [ ] **Step 3: Implement the minimal adapter and CLI**

Parse CSV values explicitly, preserve nulls, validate probability bounds, sort
championship rows descending, and write UTF-8 JSON through the CLI.

- [ ] **Step 4: Verify the adapter tests pass**

Run: `uv run pytest tests/reporting/test_dashboard.py tests/test_cli.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:
`git add src/superlig_forecast/reporting/dashboard.py src/superlig_forecast/cli.py tests/reporting/test_dashboard.py && git commit -m "feat: export dashboard data contract"`

### Task 2: Dashboard project and tested view model

**Files:**
- Create: `dashboard/.openai/hosting.json`
- Create: `dashboard/lib/dashboard-data.ts`
- Create: `dashboard/lib/dashboard-data.test.ts`
- Modify: `dashboard/package.json`
- Create: `dashboard/public/data/dashboard.json`

**Interfaces:**
- Consumes: `/data/dashboard.json`.
- Produces: `rankAtCheckpoint`, `filterFixtures`, `formatProbability`, and
  validated dashboard types used by the page.

- [ ] **Step 1: Initialize the vinext site once**

Run the Sites initializer against `dashboard/`, preserve its package manager and
lockfile, and confirm `.openai/hosting.json` exists.

- [ ] **Step 2: Write failing TypeScript view-model tests**

Test final-checkpoint ranking, earlier-checkpoint ranking, case-insensitive
fixture filtering, outcome filters, missing numeric values, and percentage
formatting.

- [ ] **Step 3: Verify the tests fail**

Run: `npm test -- --run`

Expected: FAIL because the view-model functions do not exist.

- [ ] **Step 4: Implement the minimal typed view model**

Add explicit payload types, runtime validation at the data boundary, pure
selectors, and formatting helpers.

- [ ] **Step 5: Generate the real static payload and verify tests**

Run `uv run superlig export-dashboard-data` against the five-million forecast
and twenty-season backtest, writing
`dashboard/public/data/dashboard.json`, then run `npm test -- --run`.

Expected: PASS and the payload reports 18 clubs, 306 fixtures, 7 checkpoints,
20 folds, and 5,000,000 simulations.

- [ ] **Step 6: Commit**

Run:
`git add dashboard src tests && git commit -m "feat: add typed dashboard data layer"`

### Task 3: Interactive layered-hybrid dashboard

**Files:**
- Modify: `dashboard/app/page.tsx`
- Modify: `dashboard/app/globals.css`
- Modify: `dashboard/app/layout.tsx`
- Create: `dashboard/components/championship-race.tsx`
- Create: `dashboard/components/convergence-chart.tsx`
- Create: `dashboard/components/fixture-explorer.tsx`
- Create: `dashboard/components/backtest-panel.tsx`
- Create: `dashboard/components/methodology.tsx`

**Interfaces:**
- Consumes: tested selectors from `dashboard/lib/dashboard-data.ts`.
- Produces: one responsive dashboard route with checkpoint, club, fixture, and
  methodology interactions.

- [ ] **Step 1: Write failing component contract tests**

Assert the rendered page contains the championship ranking, checkpoint control,
fixture search, validation metrics, methodology disclosure, and forecast-quality
disclaimer.

- [ ] **Step 2: Verify the component tests fail**

Run: `npm test -- --run`

Expected: FAIL because dashboard components do not exist.

- [ ] **Step 3: Build the championship and convergence layer**

Implement checkpoint selection, club visibility controls, accessible chart
tooltips, uncertainty labels, and a screen-reader data summary.

- [ ] **Step 4: Build fixture and validation layers**

Implement club search, outcome filter, paginated fixture rows, expandable match
details, aggregate score comparison, and fold history.

- [ ] **Step 5: Apply responsive visual system and metadata**

Replace starter content, remove preview skeletons and metadata, add the dark
editorial visual system, keyboard focus, reduced motion, mobile behavior, and
site-specific Open Graph metadata.

- [ ] **Step 6: Verify the site**

Run: `npm test -- --run`

Run: `npm run build`

Expected: all tests pass and the production build exits 0.

- [ ] **Step 7: Commit**

Run:
`git add dashboard README.md TODO.md && git commit -m "feat: build interactive forecast dashboard"`

### Task 4: Engine regression and production publication

**Files:**
- Modify: `README.md`
- Modify: `TODO.md`

**Interfaces:**
- Consumes: the validated dashboard source and existing engine.
- Produces: documented local run instructions and a saved, deployed Sites
  version.

- [ ] **Step 1: Update documentation**

Document the local dashboard command, data refresh command, major interactions,
and mark the deferred dashboard TODO complete.

- [ ] **Step 2: Run full verification**

Run: `uv run pytest --cov=superlig_forecast --cov-report=term -q`

Run: `uv run mypy src`

Run: `uv run ruff check src tests`

Run: `uv run ruff format --check src tests`

Run from `dashboard/`: `npm test -- --run` and `npm run build`.

Expected: every command exits 0.

- [ ] **Step 3: Publish exact committed source**

Commit the verified source, push the exact branch head to the Sites source
repository, package the validated build, save a site version, and deploy it
privately.

- [ ] **Step 4: Confirm deployment**

Poll deployment status until it succeeds and open the returned production URL.

