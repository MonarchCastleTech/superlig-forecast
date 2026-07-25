# Live Monte Carlo and GitHub Updates Design

Date: 2026-07-25
Status: approved in conversation; pending written-spec review

## Purpose

Turn the existing Süper Lig forecast dashboard into:

1. a live, user-controlled Monte Carlo player whose probabilities visibly evolve
   while it runs; and
2. a static GitHub Pages application whose real-world inputs can be refreshed by
   scheduled GitHub Actions.

This remains a forecast-quality research tool, not a betting product.

## User Experience

### Live simulation

The dashboard opens with no live run selected. The checked-in five-million-run
forecast remains available as a labelled reference result, but it is not
presented as the user's active simulation.

The live player provides:

- a target input accepting any positive integer;
- an `∞` mode that runs until the user stops it;
- Play, Pause, Resume, Stop, and Reset controls;
- current run count, rate, elapsed time, and finite-run progress;
- a selector for any exact finishing position from 1st through 18th;
- live club probability lines for the selected position;
- a live expected table and full club-by-position distribution;
- clear separation between live browser results and the published reference
  forecast.

The graph updates after completed batches. It begins noisy and visibly settles
as the sample grows. Pausing preserves state. Resume continues the same random
stream. Stop preserves the completed result. Reset clears it.

### Freshness display

The dashboard displays:

- source snapshot time;
- last successful model generation time;
- most recent completed match included;
- squad and valuation snapshot times;
- workflow status and a link to the applicable GitHub Actions run when hosted.

If an update fails, the last validated forecast remains visible with a stale or
failed-update warning. Failed or partial data never replaces a valid dataset.

## Browser Simulation Architecture

### Worker boundary

Simulation runs in a dedicated Web Worker so React rendering remains responsive.
The main thread sends:

- the team list;
- all remaining fixtures;
- home/draw/away probabilities;
- expected home and away goals;
- finite target or infinite mode;
- seed and batch-control messages.

The worker sends compact progress snapshots rather than per-season results.

### Season simulation

For every simulated season:

1. sample goals from the fixture-level expected-goal distributions;
2. award points from the sampled score;
3. accumulate goal difference and goals scored;
4. rank clubs by points, goal difference, goals scored, and a seeded stable
   fallback;
5. accumulate an 18-by-18 position-count matrix plus point and goal-difference
   sums.

This matches the current engine's documented tie-break approximation. Exact TFF
head-to-head mini-tables remain a separately identified research improvement.

### Streaming and infinite runs

The worker uses adaptive batches:

- small initial batches make the first graph changes visible quickly;
- larger later batches increase throughput;
- progress messages are throttled to keep rendering smooth;
- graph history is downsampled to a bounded number of points;
- cumulative integer counts remain authoritative and are never downsampled.

Infinite mode has no run-count ceiling. It is bounded only by the browser
session and JavaScript integer safety. The UI warns and resets before cumulative
counts approach the safe-integer boundary.

### Determinism

Each run exposes a seed. Reusing the same data snapshot, seed, and finite target
must reproduce the same final counts regardless of pause/resume behavior.

## Automatic Data Update Architecture

The design follows the public SDCofA/Monarch Castle pattern: scheduled data
generation is separate from Pages deployment.

### Workflow 1: update forecast

`.github/workflows/update-forecast.yml` runs:

- on a schedule;
- through `workflow_dispatch`;
- optionally on relevant ingestion/model code changes.

The job:

1. restores bounded HTTP and source caches;
2. fetches new match results, fixtures, squads, transfers, and valuations;
3. stores immutable timestamped source snapshots;
4. detects whether model-relevant content changed;
5. exits without generating a commit when nothing changed;
6. updates the warehouse and point-in-time features;
7. refits the model and produces the current forecast;
8. runs data-integrity, leakage, unit, backtest-sanity, and dashboard-contract
   checks;
9. writes freshness metadata;
10. commits generated dashboard data only after every gate passes.

The workflow uses one concurrency group and does not cancel an update while it
is writing a validated snapshot.

### Workflow 2: deploy Pages

`.github/workflows/deploy-pages.yml` runs only for validated main-branch changes
or manual dispatch. It:

1. checks out the repository;
2. installs locked dependencies;
3. runs dashboard tests, type checking, linting, and the static build;
4. uploads the generated static directory as the Pages artifact;
5. deploys with GitHub's official Pages actions.

It receives read-only repository permission plus the minimum Pages and ID-token
permissions. It cannot change source data.

## Source Strategy

### Free API first

The updater uses provider adapters so sources can be replaced without changing
model code.

Preferred order for fixtures and results:

1. `football-data.org` when current Süper Lig coverage is available within its
   free plan;
2. TheSportsDB free v1 API as a secondary structured source;
3. official TFF pages as the authoritative verification source and fallback.

Provider availability and coverage are checked at runtime. An API is not trusted
merely because it returns HTTP 200: team count, fixture identity, dates, scores,
and competition must pass reconciliation.

### Transfers, squads, and market values

No reviewed free API provides sufficiently complete, current Turkish transfer
and player market-value history. Therefore:

- TFF registration/squad information is preferred where available;
- current squad, transfer, and valuation pages are fetched through the existing
  source adapters with conservative rate limits and caching;
- all observations are timestamped and content-addressed;
- the last valid observation is retained when a source is unavailable;
- conflicting club/player identities are quarantined rather than guessed.

If a suitable free API later passes coverage and reconciliation tests, a new
adapter can be promoted without altering downstream features.

## GitHub Actions Safety

- Pin third-party actions to reviewed major versions initially and to commit
  SHAs before public production release.
- Use only `GITHUB_TOKEN` unless a provider explicitly requires a secret.
- Never expose source credentials to pull-request workflows.
- Set HTTP timeouts, retries, user agents, and rate limits.
- Keep raw snapshots and generated artifacts bounded by retention policy.
- Do not use `continue-on-error` for ingestion, model, validation, or deployment
  gates.
- Do not commit when generated output is byte-for-byte unchanged.

## Static GitHub Pages Compatibility

The dashboard will be exported as a static client application with repository
base-path support. It must not depend on a Node, Python, database, or Cloudflare
runtime after deployment.

The Web Worker and versioned JSON dataset are static assets. The Python engine
runs only inside Actions or locally during regeneration.

## Testing

### Worker unit tests

- deterministic seeded outcomes;
- points and score accumulation;
- complete position matrix invariants;
- finite target termination;
- infinite-mode continuation;
- pause/resume equivalence;
- reset and stale-message rejection;
- bounded graph-history sampling.

### UI tests

- finite and infinite input modes;
- Play/Pause/Resume/Stop/Reset state transitions;
- exact-position selector covers 1 through team count;
- progressive graph updates;
- live/reference labelling;
- freshness and failure states;
- keyboard and reduced-motion behavior.

### Workflow tests

- changed and unchanged source paths;
- reconciliation failure blocks publication;
- validation failure blocks commit and deployment;
- static build works under a repository subpath;
- Pages artifact contains the worker and dashboard dataset.

## Acceptance Criteria

1. The user can enter a finite count or select infinite mode.
2. Probabilities and standings visibly update during execution.
3. Every exact position is inspectable.
4. The UI remains responsive while the worker runs.
5. A finite seeded run is reproducible.
6. Infinite mode runs until explicitly paused, stopped, or reset.
7. Scheduled updates can ingest new matches, transfers, squads, and valuations.
8. Unchanged or invalid source data cannot overwrite the last valid forecast.
9. The application builds as a static GitHub Pages artifact.
10. No repository or Pages deployment is created until the user names and
    authorizes a target.

## Non-Goals

- betting advice or wagering optimization;
- live in-match event streaming;
- guaranteed exact head-to-head tie-break reproduction;
- silently substituting unverified source data;
- creating or modifying any GitHub repository before explicit authorization.
