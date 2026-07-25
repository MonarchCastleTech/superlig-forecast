# Engine to-dos

## Completed

- [x] Immutable, content-addressed source snapshots.
- [x] TFF current pages for Süper Lig, 1. Lig, 2. Lig, 3. Lig, and Cup.
- [x] Historical Transfermarkt players, valuations, appearances, and lineups.
- [x] Live 2026-27 squad pages for all 18 Süper Lig clubs.
- [x] Current player table including newly promoted Amed, Çorum, and Erzurumspor.
- [x] Source-prioritized match warehouse with 20 complete test seasons.
- [x] Point-in-time bookmaker margin removal and market/structural blending.
- [x] Strict 20-season expanding-window backtest with proper scoring rules.
- [x] Five-million-run-capable deterministic Monte Carlo engine.
- [x] Match probability, expected-goal, title probability, confidence interval,
  convergence, CSV, JSON, Parquet, and PNG outputs.
- [x] Interactive championship, convergence, fixture, validation, and
  methodology dashboard on the stable artifact contract.
- [x] Full 1st–18th position distributions, expected standings, exact-place
  probabilities, and club-by-position heatmap.
- [x] Strict 20-season preseason table backtest with position log loss, Brier
  score, expected-rank error, and uniform-baseline acceptance gates.
- [x] Static sports-style Vite dashboard with official MCT branding.
- [x] Deterministic finite/infinite browser worker with Play, Pause, Resume,
  Stop, Reset, arbitrary exact-position traces, and a live possible table.
- [x] Repository-subpath-safe build ready for GitHub Pages deployment.
- [x] Stateless scheduled updater with compact model/backtest seeds, current
  league/squad/market-value fetches, player transfer/value change detection,
  free match-feed fallback, and source-gated atomic publication.
- [x] Sequential in-season simulation: completed TFF scores seed the current
  table and only remaining fixtures are simulated in Python and the browser.

## Next research work

- [ ] Calibrate the live squad-value coefficient on historical point-in-time
  squad snapshots instead of keeping the conservative fixed value of `0.1`.
- [ ] Crawl and normalize complete official lower-tier historical schedules to
  replace the promoted-team shrinkage prior with explicit 1. Lig/2. Lig form.
- [ ] Implement exact TFF head-to-head mini-table tie-breaking for simulations
  that finish level on points; the engine currently falls through to goal
  difference and goals scored.
- [ ] Activate the scheduled free-API refresh and Pages deployment workflows
  after an exact GitHub repository is authorized.
