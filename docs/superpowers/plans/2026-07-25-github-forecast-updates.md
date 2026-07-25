# GitHub Forecast Updates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refresh matches, transfers, squads, and market values through a validated free-source-first pipeline, then publish the static dashboard through separate GitHub Actions and Pages workflows.

**Architecture:** Add replaceable structured-source adapters and strict cross-source reconciliation ahead of the existing point-in-time warehouse/model pipeline. A scheduled update workflow commits only validated changed artifacts; a separate least-privilege workflow builds and deploys the static Pages artifact.

**Tech Stack:** Python 3.13, HTTPX, Tenacity, DuckDB, Typer, pytest, GitHub Actions, GitHub Pages, Vite.

## Global Constraints

- Prefer a free structured API when it provides current, reconcilable Süper Lig coverage.
- Treat official TFF data as the authoritative match verification source and fallback.
- Retain timestamped observations; never overwrite historical transfers or market values.
- Do not deploy after any ingestion, reconciliation, model, test, or build failure.
- Do not use `continue-on-error` on a quality gate.
- Do not create or configure a remote repository until the user supplies and authorizes the exact target.
- Scheduled runs commit nothing when model-relevant output is unchanged.
- Use 5,000,000 simulations for the published current-season forecast; reuse the checked-in 20-season backtest unless model code changes.
- Pin and minimize workflow permissions.

---

### Task 1: Define normalized provider records and reconciliation

**Files:**
- Create: `src/superlig_forecast/data/structured_sources.py`
- Create: `tests/data/test_structured_sources.py`

**Interfaces:**
- Produces:
  - `StructuredMatch`
  - `ProviderBatch`
  - `reconcile_matches(primary, verification): ReconciliationReport`
  - `ReconciliationError`

- [ ] **Step 1: Write failing reconciliation tests**

```py
def test_reconcile_matches_accepts_equivalent_normalized_fixture() -> None:
    api = StructuredMatch("2026-08-14", "Galatasaray", "Fenerbahçe", 2, 1, "finished")
    tff = StructuredMatch("2026-08-14", "GALATASARAY A.Ş.", "FENERBAHÇE A.Ş.", 2, 1, "finished")
    report = reconcile_matches([api], [tff])
    assert report.matched == 1
    assert report.conflicts == ()

def test_reconcile_matches_rejects_score_conflict() -> None:
    api = StructuredMatch("2026-08-14", "A", "B", 2, 1, "finished")
    tff = StructuredMatch("2026-08-14", "A", "B", 1, 1, "finished")
    with pytest.raises(ReconciliationError, match="score conflict"):
        reconcile_matches([api], [tff])
```

- [ ] **Step 2: Run tests to verify RED**

Run `uv run pytest tests/data/test_structured_sources.py -q`.

- [ ] **Step 3: Implement normalized immutable records**

Use frozen dataclasses and explicit fields:

```py
@dataclass(frozen=True, slots=True)
class StructuredMatch:
    played_on: str
    home_team: str
    away_team: str
    home_score: int | None
    away_score: int | None
    status: Literal["scheduled", "finished", "postponed", "cancelled"]
    provider_id: str | None = None
```

Normalize names through the existing club alias registry. Reconciliation must
compare competition, date within one calendar day, clubs, status, and scores.
Finished-score conflicts are fatal.

- [ ] **Step 4: Add coverage gates**

Require exactly the expected current-season club set and reject duplicate
provider IDs or duplicate home/away/date fixtures. The report exposes
`matched`, `only_primary`, `only_verification`, and `conflicts`.

- [ ] **Step 5: Run tests and commit**

```powershell
uv run pytest tests/data/test_structured_sources.py -q
git add src/superlig_forecast/data/structured_sources.py tests/data/test_structured_sources.py
git commit -m "feat: reconcile structured football sources"
```

---

### Task 2: Add free fixture/result adapters with TFF verification

**Files:**
- Create: `src/superlig_forecast/data/football_data_org.py`
- Create: `src/superlig_forecast/data/sportsdb.py`
- Create: `tests/fixtures/football_data_matches.json`
- Create: `tests/fixtures/sportsdb_events.json`
- Create: `tests/data/test_football_data_org.py`
- Create: `tests/data/test_sportsdb.py`
- Modify: `src/superlig_forecast/data/tff.py`

**Interfaces:**
- Consumes: `StructuredMatch` and `ProviderBatch`.
- Produces:
  - `parse_football_data_matches(payload: bytes): ProviderBatch`
  - `parse_sportsdb_events(payload: bytes): ProviderBatch`
  - `TffAdapter.structured_matches(page: bytes): ProviderBatch`

- [ ] **Step 1: Add red parser tests from fixed JSON fixtures**

Test completed, scheduled, and postponed records, Turkish characters, null
scores, and wrong-competition rejection. Network access is forbidden in tests.

- [ ] **Step 2: Run parser tests to verify RED**

Run:

```powershell
uv run pytest tests/data/test_football_data_org.py tests/data/test_sportsdb.py -q
```

- [ ] **Step 3: Implement football-data.org adapter**

Use competition code `TSL`, API v4, and optional
`FOOTBALL_DATA_API_TOKEN`. If no token exists or the API denies current TSL
access, return an unavailable provider result rather than fabricated empty
coverage.

- [ ] **Step 4: Implement TheSportsDB adapter**

Use the documented free v1 key `123`, enforce 30 requests/minute, and accept
only events whose league/season/team set reconcile to the target competition.

- [ ] **Step 5: Expose structured TFF verification**

Map existing TFF parsed fixtures/results into `StructuredMatch` without changing
the raw snapshot format.

- [ ] **Step 6: Add provider-selection tests**

Create `select_match_source` with this order:

1. football-data.org when available and reconciled;
2. TheSportsDB when available and reconciled;
3. TFF-only fallback.

Any structured-provider score conflict with TFF raises
`ReconciliationError`.

- [ ] **Step 7: Run tests and commit**

```powershell
uv run pytest tests/data/test_football_data_org.py tests/data/test_sportsdb.py tests/data/test_tff.py -q
git add src/superlig_forecast/data tests/data tests/fixtures
git commit -m "feat: add free structured match providers"
```

---

### Task 3: Detect squad, transfer, and market-value changes

**Files:**
- Create: `src/superlig_forecast/data/current_changes.py`
- Create: `tests/data/test_current_changes.py`
- Modify: `src/superlig_forecast/data/transfermarkt_live.py`
- Modify: `src/superlig_forecast/cli.py`
- Modify: `tests/test_cli.py`

**Interfaces:**
- Consumes: existing normalized current-player snapshots.
- Produces:
  - `PlayerObservation`
  - `SquadChangeSet`
  - `detect_current_changes(previous, current): SquadChangeSet`

- [ ] **Step 1: Write failing change-detection tests**

```py
def test_detects_transfer_and_value_change_without_overwriting_history() -> None:
    previous = [player("p1", "Club A", 1_000_000, "2026-07-01")]
    current = [player("p1", "Club B", 1_500_000, "2026-07-25")]
    changes = detect_current_changes(previous, current)
    assert changes.transfers[0].from_club == "Club A"
    assert changes.transfers[0].to_club == "Club B"
    assert changes.valuation_changes[0].previous_value == 1_000_000
    assert len(changes.observations) == 2
```

- [ ] **Step 2: Run tests to verify RED**

Run `uv run pytest tests/data/test_current_changes.py -q`.

- [ ] **Step 3: Implement immutable observations and diffs**

Identity matching must use provider player ID first, then a quarantined
name/birth-date fallback. A player changing clubs creates a transfer observation;
a value change creates a new valuation observation. Missing players are marked
unobserved, not automatically released.

- [ ] **Step 4: Extract reusable current-squad fetching**

Refactor `fetch-current-squads` so the CLI and scheduled refresher call the same
function. Apply a source-specific user agent, 15-second connect timeout,
60-second read timeout, exponential retry for 429/5xx, and cached conditional
requests.

- [ ] **Step 5: Add CLI output contract**

`fetch-current-squads` writes a JSON manifest containing fetched, unchanged,
failed, snapshot timestamp, and source URLs. Any failed club prevents a new
complete squad snapshot from being promoted.

- [ ] **Step 6: Run tests and commit**

```powershell
uv run pytest tests/data/test_current_changes.py tests/data/test_transfermarkt_live.py tests/test_cli.py -q
git add src/superlig_forecast/data src/superlig_forecast/cli.py tests
git commit -m "feat: track current transfers and market values"
```

---

### Task 4: Add one atomic forecast-refresh command

**Files:**
- Create: `src/superlig_forecast/refresh.py`
- Create: `src/superlig_forecast/reporting/freshness.py`
- Create: `tests/test_refresh.py`
- Modify: `src/superlig_forecast/cli.py`
- Modify: `src/superlig_forecast/reporting/dashboard.py`
- Modify: `tests/reporting/test_dashboard.py`
- Modify: `dashboard/lib/dashboard-data.ts`
- Modify: `dashboard/lib/dashboard-data.test.ts`

**Interfaces:**
- Produces:
  - `RefreshConfig`
  - `RefreshResult`
  - `refresh_forecast(config): RefreshResult`
  - CLI command `superlig refresh-dashboard`
  - dashboard `freshness` object

- [ ] **Step 1: Write the failing no-change and failure tests**

Tests must prove:

```py
result = refresh_forecast(config, sources=unchanged_sources)
assert result.changed is False
assert output.read_bytes() == original_output
```

and:

```py
with pytest.raises(RefreshBlocked, match="match source reconciliation failed"):
    refresh_forecast(config, sources=conflicting_sources)
assert output.read_bytes() == original_output
```

- [ ] **Step 2: Run tests to verify RED**

Run `uv run pytest tests/test_refresh.py -q`.

- [ ] **Step 3: Implement staged atomic refresh**

Write all candidate snapshots, warehouse, forecast artifacts, and dashboard JSON
under a temporary staging directory. Run validation there. Promote the final
dashboard JSON with `Path.replace` only after success.

Use:

```py
@dataclass(frozen=True, slots=True)
class RefreshConfig:
    season: int
    simulations: int = 5_000_000
    seed: int = 202627
    output: Path = Path("dashboard/public/data/dashboard.json")
```

- [ ] **Step 4: Add freshness metadata**

Add schema fields:

```ts
freshness: {
  generated_at: string;
  match_snapshot_at: string;
  squad_snapshot_at: string;
  valuation_snapshot_at: string;
  latest_match_date: string | null;
  source_status: "fresh" | "stale" | "failed";
  source_notes: string[];
};
```

Maximum accepted ages during an active season are 24 hours for matches and
seven days for squads/values. Older critical inputs block promotion.

- [ ] **Step 5: Add the CLI command**

Expose:

```powershell
uv run superlig refresh-dashboard `
  --season 2026 `
  --simulations 5000000 `
  --output dashboard/public/data/dashboard.json
```

Exit code 0 means validated changed or validated unchanged. Data/source failure
must return non-zero.

- [ ] **Step 6: Run targeted and full Python tests, then commit**

```powershell
uv run pytest tests/test_refresh.py tests/reporting/test_dashboard.py tests/test_cli.py -q
uv run mypy src
uv run ruff check src tests
git add src tests dashboard/lib
git commit -m "feat: refresh forecast data atomically"
```

---

### Task 5: Add the scheduled update workflow and contract tests

**Files:**
- Create: `.github/workflows/update-forecast.yml`
- Create: `tests/workflows/test_github_actions.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: `superlig refresh-dashboard` from Task 4.
- Produces: validated data commits on `main`.

- [ ] **Step 1: Write the failing workflow contract**

```py
def test_update_workflow_has_strict_quality_gates() -> None:
    text = Path(".github/workflows/update-forecast.yml").read_text()
    assert "17 */6 * * *" in text
    assert "workflow_dispatch:" in text
    assert "contents: write" in text
    assert "superlig refresh-dashboard" in text
    assert "pytest" in text
    assert "mypy" in text
    assert "ruff check" in text
    assert "continue-on-error" not in text
```

- [ ] **Step 2: Run the contract to verify RED**

Run `uv run pytest tests/workflows/test_github_actions.py -q`.

- [ ] **Step 3: Implement the update workflow**

Use:

```yaml
on:
  schedule:
    - cron: "17 */6 * * *"
  workflow_dispatch:

permissions:
  contents: write

concurrency:
  group: forecast-data-update
  cancel-in-progress: false
```

Steps: checkout with full history, setup Python, install uv, `uv sync --locked`,
restore bounded source cache, run refresh, run Python tests/mypy/ruff, run
dashboard install/tests/typecheck/lint, and commit only
`dashboard/public/data/dashboard.json` plus approved snapshot manifests when
changed.

Pass optional `FOOTBALL_DATA_API_TOKEN` from repository secrets. Its absence
must trigger the documented free/fallback path.

- [ ] **Step 4: Add safe commit logic**

Use repository-local bot identity, `git diff --quiet` no-change exit, `git pull
--rebase`, and one bounded retry after a concurrent update. Do not swallow
failures.

- [ ] **Step 5: Run workflow and repository checks, then commit**

```powershell
uv run pytest tests/workflows/test_github_actions.py -q
uv run ruff check src tests
git add .github/workflows/update-forecast.yml tests/workflows .gitignore
git commit -m "ci: schedule validated forecast refreshes"
```

---

### Task 6: Add separate GitHub Pages deployment

**Files:**
- Create: `.github/workflows/deploy-pages.yml`
- Modify: `tests/workflows/test_github_actions.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: static Vite build from the live-dashboard plan.
- Produces: deployable GitHub Pages artifact; no remote activation.

- [ ] **Step 1: Extend the failing workflow contract**

Require:

```py
def test_pages_workflow_is_least_privilege_and_static() -> None:
    text = Path(".github/workflows/deploy-pages.yml").read_text()
    assert "pages: write" in text
    assert "id-token: write" in text
    assert "contents: read" in text
    assert "actions/upload-pages-artifact" in text
    assert "actions/deploy-pages" in text
    assert "npm run build:pages" in text
    assert "continue-on-error" not in text
```

- [ ] **Step 2: Run contract to verify RED**

Run `uv run pytest tests/workflows/test_github_actions.py -q`.

- [ ] **Step 3: Implement the Pages workflow**

Trigger on validated `main` pushes that affect dashboard or generated data and
on manual dispatch. Use `configure-pages`, upload `dashboard/dist`, and deploy
through the `github-pages` environment. Set Pages concurrency with
`cancel-in-progress: true`.

- [ ] **Step 4: Document repository setup without performing it**

README must state:

1. create or choose the authorized repository;
2. add optional `FOOTBALL_DATA_API_TOKEN`;
3. enable Pages source `GitHub Actions`;
4. manually run `update-forecast`;
5. confirm validation before the first Pages deployment.

Do not run `gh repo create`, change remotes, enable Pages, or push until the user
provides the exact target and explicitly authorizes those actions.

- [ ] **Step 5: Run full verification**

```powershell
uv run pytest --cov=superlig_forecast --cov-report=term -q
uv run mypy src
uv run ruff check src tests
uv run ruff format --check src tests
cd dashboard
npm test
npm run typecheck
npm run lint
```

Expected: all checks PASS; the static-build test verifies repository-subpath
assets and the dashboard data artifact.

- [ ] **Step 6: Commit**

```powershell
git add .github/workflows/deploy-pages.yml tests/workflows README.md
git commit -m "ci: deploy validated forecast dashboard to pages"
```
