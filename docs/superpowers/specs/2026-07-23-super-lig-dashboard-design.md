# Süper Lig Forecast Dashboard Design

**Status:** Approved by the existing option-C layered-hybrid dashboard decision.

## Purpose

Turn the forecasting engine's stable artifacts into an interactive research
dashboard. The dashboard explains how the 2026–27 title probabilities emerge,
how they converge across Monte Carlo checkpoints, which fixtures drive the
match-level outlook, and how the model performed in the twenty-season
walk-forward evaluation. It is a forecast-quality tool, not a betting product.

## Product structure

The first viewport is the championship race rather than generic dashboard
chrome:

1. Season, simulation count, model status, and a concise methodology note.
2. Championship probability ranking with uncertainty.
3. Interactive Monte Carlo convergence chart with checkpoint selection and
   club visibility controls.
4. Fixture explorer with club search, probability filtering, expected goals,
   and an expandable match detail view.
5. Backtest validation summary with model/baseline comparisons and fold-level
   history.
6. Methodology and data-coverage notes in a collapsible research section.

Desktop uses an asymmetric layered grid. Mobile collapses to a single reading
column while preserving filters, chart tooltips, and table readability.

## Visual direction

The interface uses a dark, editorial research-terminal aesthetic: near-black
surfaces, warm ivory text, restrained lime for calibrated probability signals,
and club-specific chart colors. Typography pairs a compact grotesk display face
with a legible sans-serif body. Dense information is grouped with whitespace,
hairline rules, and explicit labels instead of decorative cards.

Motion is limited to meaningful state changes: chart interpolation, filter
feedback, and detail disclosure. Reduced-motion preferences are respected.

## Architecture

The existing Python engine remains independent. A new dashboard export adapter
combines the forecast manifest, championship CSV, convergence CSV, fixture CSV,
and backtest JSON into one versioned JSON document. The web application consumes
only that document, so it can be built and hosted without DuckDB, private raw
snapshots, or a running Python service.

The dashboard is a vinext/React site under `dashboard/`. Data parsing and
view-model transformations live in small testable modules. The main page owns
selection state and composes focused championship, convergence, fixture, and
validation components.

## Data behavior

- The final checkpoint determines headline championship probabilities.
- Selecting a checkpoint updates both the chart cursor and ranking values.
- Club toggles change visible convergence series without changing source data.
- Fixture filters operate client-side over all 306 scheduled matches.
- Probabilities are displayed as percentages but retained as unit-interval
  numbers internally.
- Missing values render as “Not available”; they are never converted to zero.
- The dashboard displays the model seed, simulation count, run version, and
  source-alignment status.

## Error handling

The app validates the JSON schema at load time. Missing or malformed data shows
a specific recovery panel identifying the unavailable section. Empty fixture
filters produce a reset action. Non-finite probabilities are excluded and
reported in the data-quality note rather than rendered.

## Accessibility

All controls have visible labels and keyboard focus. Charts include a readable
data table summary and do not communicate by color alone. Touch targets are at
least 44 pixels, contrast meets WCAG AA, and reduced-motion preferences disable
animated transitions.

## Verification

- Python tests cover artifact normalization and invalid/missing inputs.
- TypeScript tests cover ranking, checkpoint selection, fixture filtering, and
  percentage formatting.
- The existing Python suite, type checks, lint, and formatting remain green.
- The dashboard test suite and production build pass.
- A production deployment uses the exact committed and validated source.

