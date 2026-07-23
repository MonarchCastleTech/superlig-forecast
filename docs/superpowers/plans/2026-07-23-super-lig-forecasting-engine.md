# Süper Lig Forecasting Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a point-in-time, player-aware Turkish football match model, validate it across twenty Süper Lig seasons, and generate a calibrated five-million-run forecast for the 2026–27 champion.

**Architecture:** Source adapters write immutable snapshots and normalized DuckDB/Parquet tables. Point-in-time feature builders feed a Dixon–Coles structural model, a LightGBM residual model, and timestamped margin-free market probabilities into a calibrated hybrid score distribution. A vectorized Monte Carlo engine applies versioned league rules, while a walk-forward runner produces leakage-safe validation and report artifacts.

**Tech Stack:** Python 3.13; uv; DuckDB 1.5; Polars 1.43; PyArrow 25; Pydantic 2.13; Typer 0.27; HTTPX 0.28; NumPy 2.5; SciPy 1.18; scikit-learn 1.9; LightGBM 4.7; Matplotlib 3.11; pytest 9; Hypothesis 6; Ruff 0.15; mypy 2.3.

## Global Constraints

- Score 2006–07 through 2025–26; obtain at least 2000–01 through 2005–06 match results as warm-up data.
- Ingest Süper Lig, 1. Lig, 2. Lig, 3. Lig, and Turkish Cup records with explicit per-field coverage.
- Never join a valuation, transfer, lineup, injury, suspension, result, or odds observation after the forecast cutoff.
- Keep expected-lineup and confirmed-lineup forecasts distinct.
- Exclude betting returns, staking, and betting recommendations.
- Mark a season full-market eligible only when at least 80% of Süper Lig matches have valid cutoff-time odds.
- Use five million simulations for final season-start forecasts.
- For adaptive snapshots, require a 95% Monte Carlo half-width no larger than 0.05 percentage points for every club with at least 1% championship probability, or flag the five-million cap.
- Preserve raw-source provenance, data hashes, model version, cutoff time, configuration, and random seed for every forecast.
- Produce engine, CLI, static report, JSON, and Parquet outputs only; defer the interactive dashboard.

---

## Planned File Structure

```text
pyproject.toml                         # dependencies, tools, CLI entry point
.python-version                       # Python 3.13
README.md                             # setup and reproducible commands
config/
  sources.yaml                        # source URLs, page IDs, rate limits
  competitions.yaml                   # four tiers and cup
  backtest.yaml                       # seasons, cutoffs, metrics, gates
  rules/super_lig.yaml                # season-specific league rules
src/superlig_forecast/
  __init__.py                         # package version
  cli.py                              # Typer commands
  config.py                           # typed configuration
  domain.py                           # shared immutable domain records
  data/
    fetch.py                          # retrying HTTP downloader
    snapshots.py                      # immutable snapshot manifests
    tff.py                            # official TFF parser
    transfermarkt.py                  # structured player/value adapter
    odds.py                           # historical odds import and de-vig input
    identity.py                       # canonical club/player resolution
    warehouse.py                      # DuckDB/Parquet normalization
    coverage.py                       # per-season feature coverage
  features/
    point_in_time.py                  # as-of joins
    values.py                         # inflation/position normalization
    lineups.py                        # expected and confirmed lineup features
    promotion.py                      # cross-division promoted-team priors
  modeling/
    structural.py                     # Dixon–Coles score model
    residual.py                       # LightGBM residual model
    market.py                         # margin removal and consensus
    calibration.py                    # Dirichlet and score-temperature calibration
    hybrid.py                         # coherent blended forecast
  simulation/
    rules.py                          # versioned table rules
    season.py                         # vectorized Monte Carlo
  backtest/
    splits.py                         # expanding walk-forward folds
    baselines.py                      # naive, Elo, value, market baselines
    metrics.py                        # probability and table metrics
    runner.py                         # historical replay and acceptance gates
  reporting/
    export.py                         # JSON/Parquet contract
    charts.py                         # static calibration/timeline figures
    report.py                         # Markdown/HTML research report
tests/                                # mirrors package responsibilities
tests/fixtures/                       # small frozen HTML/CSV/Parquet fixtures
```

### Task 1: Project Foundation and Typed Domain

**Files:**
- Create: `.python-version`
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/superlig_forecast/__init__.py`
- Create: `src/superlig_forecast/config.py`
- Create: `src/superlig_forecast/domain.py`
- Create: `src/superlig_forecast/cli.py`
- Create: `config/competitions.yaml`
- Test: `tests/test_config.py`
- Test: `tests/test_domain.py`

**Interfaces:**
- Produces: `Settings.load(path: Path) -> Settings`
- Produces: `ForecastMode`, `MatchRecord`, `PlayerValuation`, `OddsObservation`, `MatchForecast`
- Produces: Typer application `superlig_forecast.cli:app`

- [ ] **Step 1: Write failing configuration and domain tests**

```python
from datetime import UTC, datetime
from pathlib import Path

from superlig_forecast.config import Settings
from superlig_forecast.domain import ForecastMode, MatchRecord


def test_settings_loads_all_turkish_competitions(tmp_path: Path) -> None:
    path = tmp_path / "competitions.yaml"
    path.write_text(
        "competitions:\n"
        "  - {id: TR1, tier: 1, name: Super Lig}\n"
        "  - {id: TR2, tier: 2, name: 1. Lig}\n"
        "  - {id: TR3, tier: 3, name: 2. Lig}\n"
        "  - {id: TR4, tier: 4, name: 3. Lig}\n"
        "  - {id: TRC, tier: 0, name: Turkish Cup}\n",
        encoding="utf-8",
    )
    settings = Settings.load(path)
    assert [item.tier for item in settings.competitions] == [1, 2, 3, 4, 0]


def test_match_record_requires_timezone_aware_kickoff() -> None:
    record = MatchRecord(
        match_id="tff:317790",
        competition_id="TR1",
        season="2026-27",
        kickoff=datetime(2026, 8, 8, 18, 0, tzinfo=UTC),
        home_club_id="club:1",
        away_club_id="club:2",
        home_club_name="Galatasaray A.Ş.",
        away_club_name="Çorum FK",
        home_goals=None,
        away_goals=None,
        observed_at=datetime(2026, 7, 23, tzinfo=UTC),
    )
    assert record.is_finished is False
    assert ForecastMode.EXPECTED_LINEUP.value == "expected_lineup"
```

- [ ] **Step 2: Run the tests and verify missing-package failures**

Run: `uv run pytest tests/test_config.py tests/test_domain.py -v`

Expected: collection fails because `superlig_forecast.config` and `superlig_forecast.domain` do not exist.

- [ ] **Step 3: Add packaging, dependencies, typed settings, domain records, and CLI shell**

```toml
[project]
name = "superlig-forecast"
version = "0.1.0"
requires-python = ">=3.13,<3.14"
dependencies = [
  "duckdb>=1.5,<1.6",
  "httpx>=0.28,<0.29",
  "lightgbm>=4.7,<5",
  "matplotlib>=3.11,<4",
  "numpy>=2.5,<3",
  "orjson>=3.11,<4",
  "polars>=1.43,<2",
  "pyarrow>=25,<26",
  "pydantic>=2.13,<3",
  "pyyaml>=6.0,<7",
  "scikit-learn>=1.9,<2",
  "scipy>=1.18,<2",
  "tenacity>=9.1,<10",
  "typer>=0.27,<0.28",
]

[project.scripts]
superlig = "superlig_forecast.cli:app"

[dependency-groups]
dev = ["hypothesis>=6.160,<7", "mypy>=2.3,<3", "pytest>=9.1,<10", "pytest-cov>=7.1,<8", "ruff>=0.15,<0.16"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --strict-markers"

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.mypy]
python_version = "3.13"
strict = true
```

Implement `domain.py` as frozen Pydantic models. `MatchRecord` carries both canonical club IDs and source-observed club names. Reject naive datetimes with field validators. Add an empty Typer app with `--version`.

- [ ] **Step 4: Run foundation checks**

Run: `uv sync && uv run pytest tests/test_config.py tests/test_domain.py -v && uv run ruff check src tests && uv run mypy src`

Expected: all tests pass; Ruff and mypy report no errors.

- [ ] **Step 5: Commit**

```bash
git add .python-version pyproject.toml README.md config src tests
git commit -m "chore: establish forecasting engine foundation"
```

### Task 2: Immutable Snapshot Store and Retrying Fetcher

**Files:**
- Create: `src/superlig_forecast/data/__init__.py`
- Create: `src/superlig_forecast/data/fetch.py`
- Create: `src/superlig_forecast/data/snapshots.py`
- Test: `tests/data/test_fetch.py`
- Test: `tests/data/test_snapshots.py`

**Interfaces:**
- Consumes: timezone-aware domain timestamps from Task 1
- Produces: `Fetcher.fetch(request: FetchRequest) -> FetchResult`
- Produces: `SnapshotStore.put(result: FetchResult) -> SnapshotManifest`
- Produces: `SnapshotStore.latest(source: str) -> SnapshotManifest | None`

- [ ] **Step 1: Write failing immutability and retry tests**

```python
def test_same_payload_is_content_addressed_once(snapshot_store, fetch_result) -> None:
    first = snapshot_store.put(fetch_result)
    second = snapshot_store.put(fetch_result)
    assert first.sha256 == second.sha256
    assert first.payload_path == second.payload_path


def test_failed_fetch_does_not_replace_latest(snapshot_store, successful_result) -> None:
    saved = snapshot_store.put(successful_result)
    snapshot_store.record_failure(source="tff", url="https://www.tff.org/", reason="503")
    assert snapshot_store.latest("tff") == saved
```

- [ ] **Step 2: Verify tests fail**

Run: `uv run pytest tests/data/test_fetch.py tests/data/test_snapshots.py -v`

Expected: imports fail for `Fetcher` and `SnapshotStore`.

- [ ] **Step 3: Implement fetch and snapshot contracts**

Use HTTPX timeouts `(connect=15, read=60)`, source-specific user agents, and Tenacity exponential retry for `429`, `500`, `502`, `503`, and `504`. Store payloads at `data/raw/<source>/<sha256>.<extension>` and append JSON manifests containing URL, status, fetched time, content type, byte count, and hash. Write via a temporary sibling followed by `Path.replace`.

```python
def put(self, result: FetchResult) -> SnapshotManifest:
    digest = hashlib.sha256(result.content).hexdigest()
    payload_path = self.root / result.source / f"{digest}{result.extension}"
    payload_path.parent.mkdir(parents=True, exist_ok=True)
    if not payload_path.exists():
        temporary = payload_path.with_suffix(payload_path.suffix + ".partial")
        temporary.write_bytes(result.content)
        temporary.replace(payload_path)
    manifest = SnapshotManifest(
        source=result.source,
        url=result.url,
        fetched_at=result.fetched_at,
        status_code=result.status_code,
        content_type=result.content_type,
        byte_count=len(result.content),
        sha256=digest,
        payload_path=payload_path,
    )
    self._append_manifest(manifest)
    return manifest
```

- [ ] **Step 4: Verify focused and full checks**

Run: `uv run pytest tests/data/test_fetch.py tests/data/test_snapshots.py -v`

Expected: all snapshot/fetch tests pass, including simulated retry and failure cases.

- [ ] **Step 5: Commit**

```bash
git add src/superlig_forecast/data tests/data
git commit -m "feat: add immutable source snapshot storage"
```

### Task 3: Official TFF Four-Tier and Cup Adapter

**Files:**
- Create: `config/sources.yaml`
- Create: `src/superlig_forecast/data/tff.py`
- Create: `tests/fixtures/tff/leagues.html`
- Create: `tests/fixtures/tff/super_lig_fixture.html`
- Create: `tests/fixtures/tff/match_detail.html`
- Test: `tests/data/test_tff.py`

**Interfaces:**
- Consumes: `Fetcher`, `SnapshotStore`
- Produces: `TffAdapter.discover_competitions() -> list[TffCompetition]`
- Produces: `TffAdapter.parse_matches(html: str, observed_at: datetime) -> list[MatchRecord]`
- Produces: `TffAdapter.fetch_season(competition: TffCompetition, season: str) -> list[MatchRecord]`

- [ ] **Step 1: Freeze small HTML fixtures and write failing parser tests**

```python
def test_discovers_all_required_tff_pages(tff_adapter, leagues_html) -> None:
    found = tff_adapter.parse_competitions(leagues_html)
    assert {(item.page_id, item.tier) for item in found} >= {
        (198, 1), (142, 2), (976, 3), (971, 4), (288, 0)
    }


def test_parses_match_id_clubs_and_score(tff_adapter, fixture_html, observed_at) -> None:
    matches = tff_adapter.parse_matches(fixture_html, observed_at)
    match = next(item for item in matches if item.match_id == "tff:317790")
    assert match.competition_id == "TR1"
    assert match.home_club_name == "Galatasaray A.Ş."
    assert match.away_club_name == "Çorum FK"
```

- [ ] **Step 2: Verify parser tests fail**

Run: `uv run pytest tests/data/test_tff.py -v`

Expected: `TffAdapter` is missing.

- [ ] **Step 3: Implement the adapter and source configuration**

Configure official pages `86` (league discovery), `198` (Süper Lig fixtures), `142` (1. Lig), `976` (2. Lig), `971` (3. Lig), `288` (Turkish Cup), and archives `545`, `563`, `371`, `376`. Decode pages using the declared charset with `windows-1254` fallback. Parse match IDs from `macId`, normalize whitespace and Turkish characters, retain TFF source IDs, and fail on duplicate match IDs with conflicting clubs or scores.

```python
TFF_PAGES = {
    "TR1": {"tier": 1, "page_id": 198, "archive_page_id": 545},
    "TR2": {"tier": 2, "page_id": 142, "archive_page_id": 563},
    "TR3": {"tier": 3, "page_id": 976, "archive_page_id": 371},
    "TR4": {"tier": 4, "page_id": 971, "archive_page_id": 376},
    "TRC": {"tier": 0, "page_id": 288, "archive_page_id": 288},
}


def extract_match_ids(html: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"[?&]macId=(\d+)", html, flags=re.IGNORECASE)))


def decode_tff(payload: bytes, declared_charset: str | None) -> str:
    for encoding in [declared_charset, "windows-1254", "utf-8"]:
        if encoding:
            try:
                return payload.decode(encoding)
            except UnicodeDecodeError:
                continue
    raise ValueError("TFF payload is not valid in declared, windows-1254, or UTF-8 encoding")
```

- [ ] **Step 4: Run adapter tests and a non-persisting live smoke check**

Run: `uv run pytest tests/data/test_tff.py -v`

Run: `uv run superlig fetch-data --source tff --season 2026-27 --dry-run`

Expected: tests pass; dry-run lists all five required competition families and writes no raw payload.

- [ ] **Step 5: Commit**

```bash
git add config/sources.yaml src/superlig_forecast/data/tff.py tests/fixtures/tff tests/data/test_tff.py
git commit -m "feat: ingest official Turkish competition matches"
```

### Task 4: Player, Valuation, Transfer, Appearance, and Lineup Adapter

**Files:**
- Create: `src/superlig_forecast/data/transfermarkt.py`
- Create: `tests/fixtures/transfermarkt/schema.sql`
- Test: `tests/data/test_transfermarkt.py`

**Interfaces:**
- Consumes: public structured Transfermarkt-derived DuckDB snapshot
- Produces: `TransfermarktAdapter.read_players() -> pl.DataFrame`
- Produces: `read_valuations()`, `read_transfers()`, `read_appearances()`, `read_lineups()`, `read_games()`
- Produces: `TransfermarktAdapter.export_turkish_pyramid(output_dir: Path) -> DatasetManifest`

- [ ] **Step 1: Create a minimal fixture database and failing adapter tests**

```python
def test_valuation_keeps_effective_date_and_club(transfermarkt_adapter) -> None:
    rows = transfermarkt_adapter.read_valuations().filter(pl.col("player_id") == 10)
    assert rows.select("date").item(0, 0) == date(2025, 7, 1)
    assert rows.select("market_value_eur").item(0, 0) == 12_000_000
    assert rows.select("current_club_id").item(0, 0) == 1


def test_export_filters_required_competitions(transfermarkt_adapter, tmp_path) -> None:
    manifest = transfermarkt_adapter.export_turkish_pyramid(tmp_path)
    assert {"TR1", "TR2", "TR3", "TR4", "TRC"} <= set(manifest.requested_competitions)
    assert manifest.missing_competitions == ["TR2", "TR3", "TR4", "TRC"]
```

- [ ] **Step 2: Verify tests fail**

Run: `uv run pytest tests/data/test_transfermarkt.py -v`

Expected: adapter imports fail.

- [ ] **Step 3: Implement schema inspection and exports**

Read the public weekly DuckDB artifact from the configured URL. Validate required tables and columns before querying. Export Turkish records to partitioned Parquet by table and season. Record unavailable lower-tier tables as coverage gaps instead of fabricating rows. Keep the source player, club, competition, and game IDs for later identity resolution.

```python
REQUIRED_TABLES = {
    "players", "player_valuations", "transfers", "appearances", "games", "game_lineups"
}


def validate_schema(connection: duckdb.DuckDBPyConnection) -> None:
    present = {row[0] for row in connection.execute("show tables").fetchall()}
    missing = REQUIRED_TABLES - present
    if missing:
        raise ValueError(f"Transfermarkt snapshot missing tables: {sorted(missing)}")


def read_valuations(self) -> pl.DataFrame:
    arrow = self.connection.execute(
        """
        select player_id, date, market_value_in_eur as market_value_eur,
               current_club_id, player_club_domestic_competition_id as competition_id
        from player_valuations
        order by player_id, date
        """
    ).arrow()
    return pl.from_arrow(arrow)
```

- [ ] **Step 4: Run tests and live schema smoke check**

Run: `uv run pytest tests/data/test_transfermarkt.py -v`

Run: `uv run superlig fetch-data --source transfermarkt --schema-only`

Expected: fixture tests pass; live check reports tables for players, valuations, transfers, appearances, games, and lineups and explicitly lists missing Turkish competition coverage.

- [ ] **Step 5: Commit**

```bash
git add src/superlig_forecast/data/transfermarkt.py tests/fixtures/transfermarkt tests/data/test_transfermarkt.py
git commit -m "feat: ingest player and valuation history"
```

### Task 5: Historical Odds Import and Margin Removal Inputs

**Files:**
- Create: `src/superlig_forecast/data/odds.py`
- Create: `tests/fixtures/odds/turkey_odds.csv`
- Test: `tests/data/test_odds.py`

**Interfaces:**
- Consumes: Football-Data-format CSV or normalized OddsPortal archive CSV
- Produces: `OddsAdapter.read(path: Path, observed_at: datetime | None) -> pl.DataFrame`
- Produces: normalized `OddsObservation` records with provider and timestamp

- [ ] **Step 1: Write failing odds normalization tests**

```python
def test_wide_provider_columns_become_timestamped_rows(odds_adapter, odds_csv) -> None:
    rows = odds_adapter.read(odds_csv, observed_at=datetime(2021, 8, 12, tzinfo=UTC))
    assert set(rows["provider"]) == {"Bet365", "Pinnacle", "Average"}
    assert rows.filter(pl.col("provider") == "Bet365")["home_odds"].item() == 1.72


def test_missing_observation_time_is_rejected_for_point_in_time_use(odds_adapter, odds_csv) -> None:
    with pytest.raises(ValueError, match="observation timestamp"):
        odds_adapter.read(odds_csv, observed_at=None)
```

- [ ] **Step 2: Verify tests fail**

Run: `uv run pytest tests/data/test_odds.py -v`

Expected: `OddsAdapter` is missing.

- [ ] **Step 3: Implement import schemas and coverage flags**

Support the documented columns `Date`, `HomeTeam`, `AwayTeam`, `FTHG`, `FTAG`, and provider triplets such as `B365H/B365D/B365A`, `PSH/PSD/PSA`, and `AvgH/AvgD/AvgA`. Reject odds at or below `1.0`, retain opening/closing labels when supplied, and never infer a timestamp that the archive does not document. Store undated historical odds only in a separate `season_level_market` table that is excluded from cutoff-sensitive match forecasts.

```python
PROVIDERS = {
    "Bet365": ("B365H", "B365D", "B365A"),
    "Pinnacle": ("PSH", "PSD", "PSA"),
    "Average": ("AvgH", "AvgD", "AvgA"),
}


def normalize_odds(row: dict[str, object], observed_at: datetime) -> list[OddsObservation]:
    normalized: list[OddsObservation] = []
    for provider, columns in PROVIDERS.items():
        values = tuple(row.get(column) for column in columns)
        if any(value is None for value in values):
            continue
        odds = tuple(float(value) for value in values)
        if min(odds) <= 1.0:
            raise ValueError(f"invalid decimal odds for {provider}: {odds}")
        normalized.append(
            OddsObservation(
                match_source_key=f"{row['Date']}|{row['HomeTeam']}|{row['AwayTeam']}",
                provider=provider,
                observed_at=observed_at,
                home_odds=odds[0],
                draw_odds=odds[1],
                away_odds=odds[2],
            )
        )
    return normalized
```

- [ ] **Step 4: Run tests and produce a coverage-only import**

Run: `uv run pytest tests/data/test_odds.py -v`

Run: `uv run superlig fetch-data --source odds --input data/import/turkey_odds --coverage-only`

Expected: tests pass; command prints season coverage and full-market eligibility without training a model.

- [ ] **Step 5: Commit**

```bash
git add src/superlig_forecast/data/odds.py tests/fixtures/odds tests/data/test_odds.py
git commit -m "feat: normalize timestamped historical odds"
```

### Task 6: Canonical Identity, Warehouse, and Coverage Matrix

**Files:**
- Create: `src/superlig_forecast/data/identity.py`
- Create: `src/superlig_forecast/data/warehouse.py`
- Create: `src/superlig_forecast/data/coverage.py`
- Test: `tests/data/test_identity.py`
- Test: `tests/data/test_warehouse.py`
- Test: `tests/data/test_coverage.py`

**Interfaces:**
- Consumes: source-specific TFF, Transfermarkt, and odds records
- Produces: `IdentityResolver.resolve_club(source, source_id, name, valid_at) -> str`
- Produces: `Warehouse.build(snapshot_manifests: Sequence[SnapshotManifest]) -> BuildManifest`
- Produces: `CoverageReport.by_season() -> pl.DataFrame`

- [ ] **Step 1: Write failing temporal identity and coverage tests**

```python
def test_renamed_club_resolves_to_stable_id(resolver) -> None:
    first = resolver.resolve_club("tff", "55", "İstanbul Başakşehir FK", date(2015, 1, 1))
    second = resolver.resolve_club("tm", "6890", "Başakşehir", date(2025, 1, 1))
    assert first == second


def test_market_eligibility_requires_eighty_percent(coverage_report) -> None:
    row = coverage_report.market_eligibility(
        season="2018-19", total_matches=306, matches_with_cutoff_odds=244
    )
    assert row.coverage == pytest.approx(244 / 306)
    assert row.eligible is False
```

- [ ] **Step 2: Verify tests fail**

Run: `uv run pytest tests/data/test_identity.py tests/data/test_warehouse.py tests/data/test_coverage.py -v`

Expected: identity, warehouse, and coverage imports fail.

- [ ] **Step 3: Implement canonical maps and normalized tables**

Create DuckDB tables for competitions, clubs, club aliases, players, player aliases, matches, lineups, appearances, valuations, transfers, odds, raw manifests, and coverage. Require a manual alias row for ambiguous fuzzy matches; automatic resolution is limited to exact normalized name plus non-conflicting source IDs. Write normalized Parquet partitions and a content-addressed build manifest.

```python
def normalized_name(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value.casefold())
    ascii_text = "".join(char for char in folded if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", ascii_text).strip()


def market_eligibility(total_matches: int, matches_with_cutoff_odds: int) -> MarketEligibility:
    if total_matches <= 0:
        raise ValueError("total_matches must be positive")
    coverage = matches_with_cutoff_odds / total_matches
    return MarketEligibility(coverage=coverage, eligible=coverage >= 0.80)


WAREHOUSE_TABLES = (
    "competitions", "clubs", "club_aliases", "players", "player_aliases",
    "matches", "lineups", "appearances", "valuations", "transfers",
    "odds", "raw_manifests", "coverage",
)
```

- [ ] **Step 4: Run tests and build fixture warehouse twice**

Run: `uv run pytest tests/data/test_identity.py tests/data/test_warehouse.py tests/data/test_coverage.py -v`

Run: `uv run superlig build-snapshots --fixture-set tests/fixtures --output .test-artifacts/warehouse`

Expected: tests pass; two builds from the same fixtures produce the same manifest hash.

- [ ] **Step 5: Commit**

```bash
git add src/superlig_forecast/data tests/data
git commit -m "feat: build canonical point-in-time warehouse"
```

### Task 7: Leakage-Safe Features, Lineups, and Promotion Priors

**Files:**
- Create: `src/superlig_forecast/features/__init__.py`
- Create: `src/superlig_forecast/features/point_in_time.py`
- Create: `src/superlig_forecast/features/values.py`
- Create: `src/superlig_forecast/features/lineups.py`
- Create: `src/superlig_forecast/features/promotion.py`
- Test: `tests/features/test_point_in_time.py`
- Test: `tests/features/test_lineups.py`
- Test: `tests/features/test_promotion.py`

**Interfaces:**
- Produces: `asof_join(left, right, by, left_time, right_time) -> pl.DataFrame`
- Produces: `ValueNormalizer.fit_transform(valuations, training_end) -> pl.DataFrame`
- Produces: `LineupEstimator.predict(match_id, cutoff, mode) -> LineupProjection`
- Produces: `PromotionPrior.fit(history, training_end) -> PromotionPrior`

- [ ] **Step 1: Write failing future-leakage and promoted-team tests**

```python
def test_asof_join_never_uses_later_valuation() -> None:
    features = build_match_features(match_id="m1", cutoff=datetime(2025, 6, 1, tzinfo=UTC))
    assert features["player_value_eur"] == 8_000_000
    assert features["valuation_date"] == date(2025, 3, 1)


def test_expected_lineup_probabilities_sum_to_eleven(lineup_estimator) -> None:
    projection = lineup_estimator.predict("m1", CUTOFF_24H, ForecastMode.EXPECTED_LINEUP)
    assert sum(player.start_probability for player in projection.players) == pytest.approx(11.0)


def test_promoted_prior_uses_only_earlier_promotions(promotion_history) -> None:
    prior = PromotionPrior.fit(promotion_history, training_end=date(2018, 6, 30))
    assert max(prior.source_seasons) <= "2017-18"
```

- [ ] **Step 2: Verify tests fail**

Run: `uv run pytest tests/features -v`

Expected: feature modules are missing.

- [ ] **Step 3: Implement features**

Use backward Polars `join_asof` with exact club/player keys. Normalize `log1p(market_value_eur)` within season and position using training-period median and interquartile range. Estimate starts with an exponentially weighted selection rate, eligibility mask, positional soft constraints, and normalization to eleven starters. Build promoted-team priors from previous-tier attack/defence, value percentile, roster continuity, transfer delta, and cup-based division offsets.

```python
def asof_join(
    left: pl.DataFrame,
    right: pl.DataFrame,
    *,
    by: list[str],
    left_time: str,
    right_time: str,
) -> pl.DataFrame:
    return left.sort([*by, left_time]).join_asof(
        right.sort([*by, right_time]),
        left_on=left_time,
        right_on=right_time,
        by=by,
        strategy="backward",
        allow_exact_matches=True,
        check_sortedness=False,
    )


def robust_value_score(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(pl.col("market_value_eur").log1p().alias("log_value")).with_columns(
        (
            (pl.col("log_value") - pl.col("log_value").median().over(["season", "position"]))
            / (
                pl.col("log_value").quantile(0.75).over(["season", "position"])
                - pl.col("log_value").quantile(0.25).over(["season", "position"])
            ).clip(lower_bound=0.1)
        ).alias("value_score")
    )
```

- [ ] **Step 4: Run leakage and property tests**

Run: `uv run pytest tests/features -v`

Expected: all feature tests pass, including Hypothesis-generated cutoffs that never select a later record.

- [ ] **Step 5: Commit**

```bash
git add src/superlig_forecast/features tests/features
git commit -m "feat: create leakage-safe player and promotion features"
```

### Task 8: Dixon–Coles Structural Score Model

**Files:**
- Create: `src/superlig_forecast/modeling/__init__.py`
- Create: `src/superlig_forecast/modeling/structural.py`
- Test: `tests/modeling/test_structural.py`

**Interfaces:**
- Consumes: point-in-time match features
- Produces: `DixonColesModel.fit(matches: pl.DataFrame) -> DixonColesModel`
- Produces: `predict_score_matrix(features: MatchFeatures, max_goals: int = 10) -> np.ndarray`

- [ ] **Step 1: Write failing probability and home-advantage tests**

```python
def test_score_matrix_is_nonnegative_and_normalized(fitted_structural_model, match_features) -> None:
    matrix = fitted_structural_model.predict_score_matrix(match_features)
    assert matrix.shape == (11, 11)
    assert np.all(matrix >= 0)
    assert matrix.sum() == pytest.approx(1.0, abs=1e-10)


def test_home_advantage_increases_home_expected_goals(fitted_structural_model, match_features) -> None:
    home = fitted_structural_model.expected_goals(match_features)
    neutral = fitted_structural_model.expected_goals(match_features.model_copy(update={"neutral": True}))
    assert home.home > neutral.home
```

- [ ] **Step 2: Verify tests fail**

Run: `uv run pytest tests/modeling/test_structural.py -v`

Expected: `DixonColesModel` is missing.

- [ ] **Step 3: Implement likelihood, fitting, and score matrix**

Fit attack, defence, home advantage, time decay, and low-score correlation with SciPy L-BFGS-B. Apply sum-to-zero constraints by parameterization, clip goal rates to `[0.05, 6.0]`, compute the `0–10` matrix, and fold omitted tail mass into the boundary cells before normalization.

```python
def dixon_coles_tau(home: int, away: int, lambda_home: float, lambda_away: float, rho: float) -> float:
    if (home, away) == (0, 0):
        return 1.0 - lambda_home * lambda_away * rho
    if (home, away) == (0, 1):
        return 1.0 + lambda_home * rho
    if (home, away) == (1, 0):
        return 1.0 + lambda_away * rho
    if (home, away) == (1, 1):
        return 1.0 - rho
    return 1.0


def score_matrix(lambda_home: float, lambda_away: float, rho: float, max_goals: int = 10) -> np.ndarray:
    home = poisson.pmf(np.arange(max_goals + 1), np.clip(lambda_home, 0.05, 6.0))
    away = poisson.pmf(np.arange(max_goals + 1), np.clip(lambda_away, 0.05, 6.0))
    matrix = np.outer(home, away)
    for home_goals in range(2):
        for away_goals in range(2):
            matrix[home_goals, away_goals] *= dixon_coles_tau(
                home_goals, away_goals, lambda_home, lambda_away, rho
            )
    return matrix / matrix.sum()
```

- [ ] **Step 4: Run model tests**

Run: `uv run pytest tests/modeling/test_structural.py -v`

Expected: probability, low-score correction, parameter-identifiability, and serialization tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/superlig_forecast/modeling tests/modeling/test_structural.py
git commit -m "feat: add structural score probability model"
```

### Task 9: Residual, Market, Calibration, and Hybrid Forecast

**Files:**
- Create: `src/superlig_forecast/modeling/residual.py`
- Create: `src/superlig_forecast/modeling/market.py`
- Create: `src/superlig_forecast/modeling/calibration.py`
- Create: `src/superlig_forecast/modeling/hybrid.py`
- Test: `tests/modeling/test_market.py`
- Test: `tests/modeling/test_calibration.py`
- Test: `tests/modeling/test_hybrid.py`

**Interfaces:**
- Produces: `remove_margin(decimal_odds: np.ndarray, method="power") -> np.ndarray`
- Produces: `MarketConsensus.from_observations(observations, cutoff) -> MarketConsensus | None`
- Produces: `ResidualModel.fit_oof(features, targets, folds) -> ResidualModel`
- Produces: `HybridModel.predict(features, market) -> MatchForecast`

- [ ] **Step 1: Write failing coherence and cutoff tests**

```python
def test_power_devig_returns_probabilities_summing_to_one() -> None:
    fair = remove_margin(np.array([1.72, 3.70, 5.20]), method="power")
    assert fair.sum() == pytest.approx(1.0)
    assert np.all(fair > 0)


def test_market_consensus_ignores_observation_after_cutoff() -> None:
    consensus = MarketConsensus.from_observations(ODDS_ROWS, cutoff=CUTOFF_24H)
    assert consensus is not None
    assert consensus.latest_observed_at <= CUTOFF_24H


def test_hybrid_returns_coherent_score_and_one_x_two_probabilities(hybrid_model, features) -> None:
    forecast = hybrid_model.predict(features, market=None)
    matrix = np.asarray(forecast.score_probabilities)
    assert forecast.home_probability == pytest.approx(np.tril(matrix, -1).sum())
    assert forecast.draw_probability == pytest.approx(np.trace(matrix))
```

- [ ] **Step 2: Verify tests fail**

Run: `uv run pytest tests/modeling/test_market.py tests/modeling/test_calibration.py tests/modeling/test_hybrid.py -v`

Expected: market, calibration, and hybrid modules are missing.

- [ ] **Step 3: Implement the hybrid**

Train LightGBM residual regressors only on out-of-fold structural predictions and point-in-time features. Convert residual goal adjustments back into a score matrix. Fit blend weights by prior-period log loss. Implement multiclass Dirichlet calibration with multinomial logistic regression over log probabilities and fit one positive temperature for the score matrix. Reconstruct the final 1X2 values from the calibrated score matrix.

```python
def remove_margin(decimal_odds: np.ndarray, method: str = "power") -> np.ndarray:
    if np.any(decimal_odds <= 1.0):
        raise ValueError("decimal odds must exceed 1.0")
    inverse = 1.0 / np.asarray(decimal_odds, dtype=float)
    if method != "power":
        raise ValueError(f"unsupported margin-removal method: {method}")
    exponent = brentq(lambda power: np.power(inverse, power).sum() - 1.0, 0.01, 10.0)
    fair = np.power(inverse, exponent)
    return fair / fair.sum()


def one_x_two_from_matrix(matrix: np.ndarray) -> np.ndarray:
    return np.array([np.tril(matrix, -1).sum(), np.trace(matrix), np.triu(matrix, 1).sum()])


def apply_temperature(matrix: np.ndarray, temperature: float) -> np.ndarray:
    logits = np.log(np.clip(matrix, 1e-15, 1.0)) / temperature
    calibrated = np.exp(logits - logits.max())
    return calibrated / calibrated.sum()
```

- [ ] **Step 4: Run focused model tests**

Run: `uv run pytest tests/modeling -v`

Expected: all structural, market, calibration, serialization, cutoff, and coherence tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/superlig_forecast/modeling tests/modeling
git commit -m "feat: combine residual market and calibrated forecasts"
```

### Task 10: Versioned League Rules and Vectorized Monte Carlo

**Files:**
- Create: `config/rules/super_lig.yaml`
- Create: `src/superlig_forecast/simulation/__init__.py`
- Create: `src/superlig_forecast/simulation/rules.py`
- Create: `src/superlig_forecast/simulation/season.py`
- Test: `tests/simulation/test_rules.py`
- Test: `tests/simulation/test_season.py`
- Test: `tests/simulation/test_convergence.py`

**Interfaces:**
- Produces: `LeagueRules.for_season(season: str) -> LeagueRules`
- Produces: `SeasonSimulator.simulate(fixtures, forecasts, n, seed) -> SimulationResult`
- Produces: `SeasonSimulator.simulate_until_converged(...) -> SimulationResult`

- [ ] **Step 1: Write failing rules, determinism, and convergence tests**

```python
def test_same_seed_produces_identical_champion_counts(simulator, fixtures, forecasts) -> None:
    first = simulator.simulate(fixtures, forecasts, n=100_000, seed=202627)
    second = simulator.simulate(fixtures, forecasts, n=100_000, seed=202627)
    assert first.champion_counts == second.champion_counts


def test_table_points_equal_simulated_results(simulator, fixtures, forecasts) -> None:
    result = simulator.simulate(fixtures, forecasts, n=1, seed=7, retain_first=1)
    assert result.tables[0].points.sum() == 2 * result.draw_counts[0] + 3 * result.decisive_counts[0]


def test_adaptive_run_doubles_until_half_width_threshold(simulator, fixtures, forecasts) -> None:
    result = simulator.simulate_until_converged(fixtures, forecasts, seed=9)
    assert result.n_simulations in {100_000, 200_000, 400_000, 800_000, 1_600_000, 3_200_000, 5_000_000}
    assert result.converged or result.n_simulations == 5_000_000
```

- [ ] **Step 2: Verify tests fail**

Run: `uv run pytest tests/simulation -v`

Expected: simulation modules are missing.

- [ ] **Step 3: Implement rules and chunked simulation**

Load per-season league size, points, deductions, and ordered tie-break keys from YAML. Validate each historical rules entry has a source URL and retrieval date. Sample categorical scorelines from flattened score matrices in chunks sized from a configurable memory budget. Aggregate points, goals, head-to-head mini-tables where required, final positions, and champion counts without retaining every simulation.

```python
def sample_score_indices(
    matrix: np.ndarray, n: int, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    side = matrix.shape[0]
    flat = rng.choice(matrix.size, size=n, p=matrix.ravel())
    return flat // side, flat % side


def monte_carlo_half_width(champion_count: int, n: int) -> float:
    probability = champion_count / n
    return 1.96 * math.sqrt(probability * (1.0 - probability) / n)


SIMULATION_STEPS = (100_000, 200_000, 400_000, 800_000, 1_600_000, 3_200_000, 5_000_000)


def has_converged(champion_counts: np.ndarray, n: int) -> bool:
    probabilities = champion_counts / n
    relevant = probabilities >= 0.01
    half_widths = 1.96 * np.sqrt(probabilities * (1.0 - probabilities) / n)
    return bool(np.all(half_widths[relevant] <= 0.0005))
```

- [ ] **Step 4: Run correctness and one-million performance checks**

Run: `uv run pytest tests/simulation -v`

Run: `uv run superlig forecast-season --fixture-set tests/fixtures/mini-season --simulations 1000000 --seed 42 --benchmark`

Expected: tests pass; benchmark reports throughput, peak memory, and Monte Carlo half-width.

- [ ] **Step 5: Commit**

```bash
git add config/rules src/superlig_forecast/simulation tests/simulation
git commit -m "feat: simulate seasons with versioned league rules"
```

### Task 11: Walk-Forward Backtest, Baselines, Metrics, and Gates

**Files:**
- Create: `config/backtest.yaml`
- Create: `src/superlig_forecast/backtest/__init__.py`
- Create: `src/superlig_forecast/backtest/splits.py`
- Create: `src/superlig_forecast/backtest/baselines.py`
- Create: `src/superlig_forecast/backtest/metrics.py`
- Create: `src/superlig_forecast/backtest/runner.py`
- Test: `tests/backtest/test_splits.py`
- Test: `tests/backtest/test_metrics.py`
- Test: `tests/backtest/test_runner.py`

**Interfaces:**
- Produces: `walk_forward_folds(seasons, warmup_end) -> list[BacktestFold]`
- Produces: naive, Elo, value-only, market-only, structural, and hybrid predictors
- Produces: `BacktestRunner.run(config) -> BacktestResult`
- Produces: `AcceptanceGate.evaluate(result) -> GateResult`

- [ ] **Step 1: Write failing fold, leakage, metric, and gate tests**

```python
def test_each_fold_trains_only_before_test_season() -> None:
    folds = walk_forward_folds(SEASONS_2000_TO_2026, warmup_end="2005-06")
    assert len(folds) == 20
    assert folds[0].test_season == "2006-07"
    assert all(max(fold.train_seasons) < fold.test_season for fold in folds)


def test_gate_requires_both_primary_point_estimates_to_improve() -> None:
    gate = AcceptanceGate.evaluate(RESULT_WITH_WORSE_BRIER)
    assert gate.passed is False
    assert "Brier" in gate.failures


def test_matchday_snapshot_precedes_new_result(backtest_runner) -> None:
    result = backtest_runner.run(MINI_BACKTEST)
    snapshot = result.snapshot_before("historical-match-2")
    assert "historical-match-2" not in snapshot.completed_match_ids
```

- [ ] **Step 2: Verify tests fail**

Run: `uv run pytest tests/backtest -v`

Expected: backtest modules are missing.

- [ ] **Step 3: Implement replay, metrics, baselines, and acceptance logic**

Create exactly twenty expanding folds. Fit tuning and calibration inside prior data. Save preseason, expected-lineup, confirmed-lineup, and post-matchday snapshots. Compute multiclass log loss, Brier, ranked probability score, expected calibration error, score log loss, champion Brier/log loss, table rank correlation, position error, and interval coverage. Use season-block bootstrap with a fixed recorded seed. Implement every numeric gate from the design specification.

```python
def walk_forward_folds(seasons: list[str], warmup_end: str) -> list[BacktestFold]:
    folds: list[BacktestFold] = []
    for test_season in seasons:
        if test_season <= warmup_end:
            continue
        train = tuple(season for season in seasons if season < test_season)
        folds.append(BacktestFold(train_seasons=train, test_season=test_season))
    if len(folds) != 20:
        raise ValueError(f"expected 20 scored folds, found {len(folds)}")
    return folds


def brier_score_multiclass(probabilities: np.ndarray, target: np.ndarray) -> float:
    observed = np.eye(probabilities.shape[1])[target]
    return float(np.mean(np.sum((probabilities - observed) ** 2, axis=1)))


def primary_gate(metrics: MetricComparison) -> list[str]:
    failures: list[str] = []
    if metrics.hybrid_log_loss >= metrics.best_non_market_log_loss:
        failures.append("log loss did not improve over the best non-market baseline")
    if metrics.hybrid_brier >= metrics.best_non_market_brier:
        failures.append("Brier score did not improve over the best non-market baseline")
    if metrics.market_log_loss is not None and metrics.hybrid_log_loss > metrics.market_log_loss + 0.005:
        failures.append("log loss exceeded the market-only tolerance")
    return failures
```

- [ ] **Step 4: Run mini backtest and full unit suite**

Run: `uv run pytest tests/backtest -v`

Run: `uv run superlig backtest --fixture-set tests/fixtures/mini-backtest --output .test-artifacts/backtest`

Expected: tests pass; mini backtest emits metrics for every baseline, snapshot manifests, and a gate result.

- [ ] **Step 5: Commit**

```bash
git add config/backtest.yaml src/superlig_forecast/backtest tests/backtest
git commit -m "feat: add leakage-safe walk-forward backtesting"
```

### Task 12: Exports, Static Report, CLI Completion, and Real-Data Runbook

**Files:**
- Create: `src/superlig_forecast/reporting/__init__.py`
- Create: `src/superlig_forecast/reporting/export.py`
- Create: `src/superlig_forecast/reporting/charts.py`
- Create: `src/superlig_forecast/reporting/report.py`
- Modify: `src/superlig_forecast/cli.py`
- Modify: `README.md`
- Test: `tests/reporting/test_export.py`
- Test: `tests/reporting/test_report.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Produces: `export_forecast(result, output_dir) -> ExportManifest`
- Produces: `build_report(backtest, forecast, output_dir) -> Path`
- Completes CLI commands: `fetch-data`, `build-snapshots`, `train-model`, `backtest`, `forecast-match`, `forecast-season`, `export-results`

- [ ] **Step 1: Write failing export and CLI tests**

```python
def test_timeline_export_has_dashboard_contract(exported_timeline: pl.DataFrame) -> None:
    assert exported_timeline.columns == [
        "snapshot_id", "observed_at", "season", "club_id",
        "champion_probability", "delta_probability", "result_delta",
        "squad_delta", "lineup_delta", "market_delta", "interaction_delta",
        "model_version", "data_hash",
    ]


def test_cli_forecast_season_records_seed(runner, mini_config) -> None:
    result = runner.invoke(
        app,
        ["forecast-season", "--config", str(mini_config), "--simulations", "100000", "--seed", "42"],
    )
    assert result.exit_code == 0
    manifest = json.loads(Path(result.stdout.strip()).read_text(encoding="utf-8"))
    assert manifest["seed"] == 42
```

- [ ] **Step 2: Verify tests fail**

Run: `uv run pytest tests/reporting tests/test_cli.py -v`

Expected: reporting modules and completed CLI commands are missing.

- [ ] **Step 3: Implement exports, charts, report, and commands**

Export match forecasts, position probabilities, champion probabilities, timelines, coverage, metrics, gates, manifests, and explanatory one-family-at-a-time deltas as Parquet plus compact JSON. Generate calibration, baseline-comparison, promoted-team, Monte Carlo convergence, and championship-timeline charts. Build a Markdown and HTML report that labels observed data, model estimates, missingness, and failed gates.

```python
TIMELINE_COLUMNS = [
    "snapshot_id", "observed_at", "season", "club_id",
    "champion_probability", "delta_probability", "result_delta",
    "squad_delta", "lineup_delta", "market_delta", "interaction_delta",
    "model_version", "data_hash",
]


def export_timeline(frame: pl.DataFrame, output_dir: Path) -> Path:
    missing = set(TIMELINE_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"timeline export missing columns: {sorted(missing)}")
    path = output_dir / "championship_timeline.parquet"
    output_dir.mkdir(parents=True, exist_ok=True)
    frame.select(TIMELINE_COLUMNS).write_parquet(path, compression="zstd")
    return path


def write_manifest(manifest: ExportManifest, output_dir: Path) -> Path:
    path = output_dir / "manifest.json"
    path.write_bytes(orjson.dumps(manifest.model_dump(mode="json"), option=orjson.OPT_INDENT_2))
    return path
```

- [ ] **Step 4: Run full verification on fixtures**

Run: `uv run pytest --cov=superlig_forecast --cov-report=term-missing`

Run: `uv run ruff check src tests && uv run ruff format --check src tests`

Run: `uv run mypy src`

Run: `uv run superlig backtest --fixture-set tests/fixtures/mini-backtest --output .test-artifacts/final`

Expected: tests, lint, formatting, and type checks pass; the fixture report, figures, JSON, Parquet, and manifests are generated.

- [ ] **Step 5: Add and execute the real-data runbook**

Document and run:

```bash
uv run superlig fetch-data --config config/sources.yaml --seasons 2000-01:2026-27
uv run superlig build-snapshots --config config/sources.yaml
uv run superlig backtest --config config/backtest.yaml --output artifacts/backtest
uv run superlig forecast-season --season 2026-27 --simulations 5000000 --seed 202627 --output artifacts/forecast-2026-27
uv run superlig export-results --backtest artifacts/backtest --forecast artifacts/forecast-2026-27 --output artifacts/report
```

Expected: the coverage matrix explicitly identifies every unavailable source-season feature; twenty scored folds complete only if the required warm-up and results coverage exists; the five-million forecast records convergence; the report states whether the hybrid passed or failed each quality gate.

- [ ] **Step 6: Commit**

```bash
git add src/superlig_forecast/reporting src/superlig_forecast/cli.py tests/reporting tests/test_cli.py README.md
git commit -m "feat: deliver reproducible forecast engine outputs"
```

## Final Verification

- [ ] Run: `uv run pytest --cov=superlig_forecast --cov-report=term-missing`
- [ ] Run: `uv run ruff check src tests`
- [ ] Run: `uv run ruff format --check src tests`
- [ ] Run: `uv run mypy src`
- [ ] Run: `git status --short`
- [ ] Confirm the 20-season backtest report distinguishes the 20-season value/results evaluation from the coverage-qualified full-market evaluation.
- [ ] Confirm the 2026–27 manifest records exactly 5,000,000 simulations, seed `202627`, model version, data hash, cutoff time, and convergence interval.
- [ ] Confirm no dashboard or betting-return code is present.
