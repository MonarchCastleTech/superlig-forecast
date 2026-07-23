# Süper Lig Table Probabilities Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add full 1st–18th position probabilities and a strict twenty-season
position-distribution backtest to the engine and dashboard.

**Architecture:** Extend the chunked simulator with compact club × position
counts and team aggregates. A separate preseason walk-forward evaluator scores
those distributions, while the dashboard export combines current and backtest
artifacts into the existing static JSON boundary.

**Tech Stack:** Python, NumPy, pytest, Typer, React, TypeScript, Vitest, CSS.

## Global Constraints

- Do not retain five million individual simulated tables.
- Preserve deterministic checkpoint behavior.
- Train each backtest fold only on earlier seasons.
- Label expected standings as marginal estimates.
- Preserve missing values and expose exact 17th-place probability.

---

### Task 1: Full-position Monte Carlo aggregation

**Files:**
- Modify: `src/superlig_forecast/simulation/season.py`
- Modify: `tests/simulation/test_season.py`
- Modify: `src/superlig_forecast/cli.py`

- [ ] Write failing tests for position counts, position totals, point sums, goal
  difference sums, and champion-count compatibility.
- [ ] Run the targeted tests and confirm missing aggregates cause the failure.
- [ ] Aggregate ranked positions in each chunk and export position and expected
  standings CSV files.
- [ ] Run simulator and CLI tests until green.

### Task 2: Strict position backtest

**Files:**
- Create: `src/superlig_forecast/backtest/positions.py`
- Create: `tests/backtest/test_positions.py`
- Modify: `src/superlig_forecast/cli.py`

- [ ] Write failing synthetic-season tests for leakage-safe folds, actual table
  reconstruction, probability normalization, and position metrics.
- [ ] Implement preseason fixture simulation and Jeffreys-smoothed position log
  loss, Brier, expected-position error, and uniform baselines.
- [ ] Add `backtest-positions` CLI output with fold and aggregate acceptance
  checks.
- [ ] Run all twenty real folds and save the artifact and chart.

### Task 3: Interactive standings dashboard

**Files:**
- Modify: `src/superlig_forecast/reporting/dashboard.py`
- Modify: `tests/reporting/test_dashboard.py`
- Modify: `dashboard/lib/dashboard-data.ts`
- Modify: `dashboard/lib/dashboard-data.test.ts`
- Create: `dashboard/components/standings-panel.tsx`
- Modify: `dashboard/components/dashboard-app.tsx`
- Modify: `dashboard/app/globals.css`

- [ ] Write failing Python and TypeScript contract tests for current positions,
  expected standings, exact 17th probability, and position-backtest metrics.
- [ ] Extend the static dashboard payload and typed selectors.
- [ ] Build the expected table, position heatmap, club detail, and validation
  evidence strip.
- [ ] Regenerate five-million and twenty-season artifacts.
- [ ] Run complete Python and frontend verification and deploy the exact
  committed source as a new private Sites version.

