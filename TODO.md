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

## Next research work

- [ ] Calibrate the live squad-value coefficient on historical point-in-time
  squad snapshots instead of keeping the conservative fixed value of `0.1`.
- [ ] Crawl and normalize complete official lower-tier historical schedules to
  replace the promoted-team shrinkage prior with explicit 1. Lig/2. Lig form.
- [ ] Implement exact TFF head-to-head mini-table tie-breaking for simulations
  that finish level on points; the engine currently falls through to goal
  difference and goals scored.
- [ ] Add sequential in-season updates after each completed match so the
  probability timeline reflects observed 2026-27 results.
- [ ] Build the deferred interactive dashboard on the stable artifact contracts.
