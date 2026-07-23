# Süper Lig Table Probability Design

**Status:** Approved by the request to add possible standings with backtesting.

## Outcome

The simulator will retain the full finishing-position distribution for every
club instead of discarding all ranks except first place. The dashboard will show
an expected standings table, exact 1st–18th probabilities, a heatmap, expected
points, top-four probability, relegation probability, and the probability of
finishing exactly 17th.

The expected table is a marginal summary, not a claim that its complete ordering
is the single most likely joint table. Each row therefore keeps the underlying
position distribution visible.

## Simulation contract

For every Monte Carlo chunk, rank clubs by the existing points, goal-difference,
and goals-scored rules. Aggregate:

- counts for every club × finishing-position pair;
- total points by club;
- total goal difference by club; and
- championship counts as the first-position column.

All aggregates remain cumulative across checkpoints and deterministic for a
fixed seed. The engine will export long-form position probabilities and an
expected-standings summary without retaining individual simulated tables.

## Backtest

Run a strict preseason expanding-window evaluation for each season from
2006–07 through 2025–26. Fit the team-strength model only on earlier seasons,
predict every fixture in the target season, simulate the scheduled season, and
compare the position distribution with the table reconstructed from actual
results.

Score each club-season with position log loss, multiclass Brier score, and
absolute expected-position error. Compare against a uniform-position baseline.
Use Jeffreys smoothing only for backtest scoring to avoid infinite log loss from
finite simulation samples. Publish fold-level and aggregate metrics.

## Dashboard

Add a standings section after the championship race:

- expected standings ordered by mean finishing position;
- expected points and goal difference;
- most likely and median position;
- top-four, 17th-place, and relegation probabilities;
- selectable club detail with an eighteen-position probability heatmap; and
- a position-backtest evidence strip.

The existing championship, convergence, fixture, and match-backtest views remain
unchanged.

