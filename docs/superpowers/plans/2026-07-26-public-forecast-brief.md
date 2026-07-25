# Public Süper Lig Forecast Brief Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish an end-user MCT Süper Lig forecast brief with daily validated results, polished probability graphics, winner/draw match outlooks, an academic methodology, and no user-run simulation controls.

**Architecture:** Keep the existing versioned dashboard JSON as the sole public data contract and render only its latest validated five-million-run artifact. Replace simulator state with pure presentation helpers and focused public components. Deploy the forecast from a new `MonarchCastleTech/superlig-forecast` repository and register it in the governed `MonarchCastleTech.github.io` product portfolio.

**Tech Stack:** React 19, TypeScript 5.9, Vite 8, Recharts 3, Vitest, Testing Library, Python 3.13, Typer, GitHub Actions, GitHub Pages.

## Global Constraints

- Public copy is English; official Turkish club names remain unchanged.
- The dashboard displays one daily forecast and has no simulation target or user-run simulation controls.
- The permanent notice says the product is not betting advice and is not a guarantee.
- Match forecasts display home/draw/away probabilities and a most-likely winner or draw, never an exact score.
- MCT branding uses the existing organization-controlled asset at `dashboard/public/brand/mct-icon.png`.
- The production URL is `https://monarchcastletech.github.io/superlig-forecast/`.
- The source repository is `https://github.com/MonarchCastleTech/superlig-forecast`.

---

### Task 1: Public forecast presentation helpers

**Files:**
- Modify: `dashboard/lib/dashboard-data.ts`
- Test: `dashboard/lib/dashboard-data.test.ts`

**Interfaces:**
- Consumes: `FixtureRow`, `DashboardPayload.freshness.generated_at`
- Produces: `classifyMatchOutcome(fixture: FixtureRow): MatchOutcome`, `formatForecastUpdate(value: string): string`

- [ ] **Step 1: Write failing helper tests**

```ts
test("labels the highest 1X2 outcome without predicting a score", () => {
  expect(classifyMatchOutcome(fixture)).toEqual({
    label: "Galatasaray SK most likely winner",
    confidence: "Clear model edge",
    outcome: "home",
  });
});

test("calls a narrow plurality too close to call", () => {
  expect(classifyMatchOutcome({ ...fixture, home_win_probability: 0.36,
    draw_probability: 0.34, away_win_probability: 0.30 }).confidence)
    .toBe("Too close to call");
});

test("formats the publication time for Istanbul", () => {
  expect(formatForecastUpdate("2026-07-26T03:00:00Z"))
    .toContain("26 Jul 2026");
});
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `cd dashboard && npm run test:unit -- lib/dashboard-data.test.ts`

Expected: FAIL because `classifyMatchOutcome` and `formatForecastUpdate` are not exported.

- [ ] **Step 3: Implement the pure helpers**

```ts
export type MatchOutcome = {
  outcome: "home" | "draw" | "away";
  label: string;
  confidence: "Too close to call" | "Slight edge" | "Clear model edge";
};

export function classifyMatchOutcome(fixture: FixtureRow): MatchOutcome {
  const outcomes = [
    { outcome: "home" as const, probability: fixture.home_win_probability },
    { outcome: "draw" as const, probability: fixture.draw_probability },
    { outcome: "away" as const, probability: fixture.away_win_probability },
  ].sort((a, b) => b.probability - a.probability);
  const margin = outcomes[0].probability - outcomes[1].probability;
  return {
    outcome: outcomes[0].outcome,
    label: outcomes[0].outcome === "draw"
      ? "Draw most likely"
      : `${outcomes[0].outcome === "home" ? fixture.home_team : fixture.away_team} most likely winner`,
    confidence: margin < 0.05
      ? "Too close to call"
      : margin <= 0.12 ? "Slight edge" : "Clear model edge",
  };
}

export function formatForecastUpdate(value: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Europe/Istanbul",
    timeZoneName: "short",
  }).format(new Date(value));
}
```

- [ ] **Step 4: Run helper tests and verify GREEN**

Run: `cd dashboard && npm run test:unit -- lib/dashboard-data.test.ts`

Expected: all `dashboard-data` tests pass.

- [ ] **Step 5: Commit**

```bash
git add dashboard/lib/dashboard-data.ts dashboard/lib/dashboard-data.test.ts
git commit -m "feat: add public forecast presentation helpers"
```

### Task 2: End-user shell, timestamp, and permanent notice

**Files:**
- Modify: `dashboard/components/dashboard-app.tsx`
- Modify: `dashboard/components/dashboard-app.test.tsx`
- Delete: `dashboard/components/live-simulation-panel.tsx`
- Delete: `dashboard/components/live-simulation-panel.test.tsx`
- Delete: `dashboard/components/live-probability-chart.tsx`
- Delete: `dashboard/hooks/use-live-simulation.ts`
- Delete: `dashboard/lib/live-worker-protocol.ts`
- Delete: `dashboard/lib/live-worker-protocol.test.ts`
- Delete: `dashboard/lib/live-worker-runner.ts`
- Delete: `dashboard/lib/live-worker-runner.test.ts`
- Delete: `dashboard/lib/live-simulation.ts`
- Delete: `dashboard/lib/live-simulation.test.ts`
- Delete: `dashboard/workers/season-simulator.worker.ts`

**Interfaces:**
- Consumes: `DashboardPayload`, `formatForecastUpdate`
- Produces: static public page shell with `data-testid="forecast-updated"` and `role="note"`

- [ ] **Step 1: Replace the app test with public behavior assertions**

```tsx
render(<DashboardApp data={data} />);
expect(screen.getByTestId("forecast-updated")).toHaveTextContent("Updated");
expect(screen.getByRole("note")).toHaveTextContent("not betting advice");
expect(screen.getByRole("note")).toHaveTextContent("not a guarantee");
expect(screen.queryByText(/simulation target/i)).not.toBeInTheDocument();
expect(screen.queryByRole("button", { name: /play/i })).not.toBeInTheDocument();
```

- [ ] **Step 2: Run the app test and verify RED**

Run: `cd dashboard && npm run test:unit -- components/dashboard-app.test.tsx`

Expected: FAIL because the current page renders simulator status and controls and lacks the permanent notice.

- [ ] **Step 3: Remove browser-simulation imports and render the static shell**

```tsx
const updateLabel = formatForecastUpdate(data.freshness.generated_at);
const leader = data.expected_standings[0];

<span className="model-status" data-testid="forecast-updated">
  <i /> Updated {updateLabel}
</span>
<aside className="forecast-notice" role="note">
  <strong>Research forecast</strong>
  <span>This is not betting advice and is not a guarantee of any result.</span>
</aside>
```

Use `data.championship`, `data.positions`, and `data.expected_standings` directly.
Remove all `useLiveSimulation`, `deriveLiveTables`, and live controller paths.

- [ ] **Step 4: Delete the unused worker/controller files**

Delete only the files listed in this task. Remove any imports found by:

Run: `rg "live-simulation|live-worker|season-simulator.worker|useLiveSimulation" dashboard -g '!node_modules'`

Expected: no matches after the deletions and import cleanup.

- [ ] **Step 5: Run app tests and typecheck**

Run: `cd dashboard && npm run test:unit -- components/dashboard-app.test.tsx && npm run typecheck`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add dashboard
git commit -m "feat: replace simulator UI with daily forecast brief"
```

### Task 3: Match winner and draw outlook

**Files:**
- Create: `dashboard/components/match-outlook.tsx`
- Create: `dashboard/components/match-outlook.test.tsx`
- Modify: `dashboard/components/dashboard-app.tsx`
- Delete: `dashboard/components/fixture-explorer.tsx`

**Interfaces:**
- Consumes: `FixtureRow[]`, `classifyMatchOutcome`
- Produces: `MatchOutlook({ fixtures }: { fixtures: FixtureRow[] })`

- [ ] **Step 1: Write failing component tests**

```tsx
render(<MatchOutlook fixtures={[fixture]} />);
expect(screen.getByText("Galatasaray SK most likely winner")).toBeVisible();
expect(screen.getByText("Clear model edge")).toBeVisible();
expect(screen.getByText("Home")).toBeVisible();
expect(screen.getByText("Draw")).toBeVisible();
expect(screen.getByText("Away")).toBeVisible();
expect(screen.queryByText(/score/i)).not.toBeInTheDocument();
```

- [ ] **Step 2: Run and verify RED**

Run: `cd dashboard && npm run test:unit -- components/match-outlook.test.tsx`

Expected: FAIL because `MatchOutlook` does not exist.

- [ ] **Step 3: Implement searchable fixture cards**

The component:

- sorts fixtures with the clearest probability edge first;
- provides team-name search;
- renders the outcome label and confidence badge;
- renders three proportional bars labelled Home, Draw, and Away;
- formats percentages to one decimal place;
- contains no score or betting language.

Core card markup:

```tsx
const prediction = classifyMatchOutcome(fixture);
<article className="match-card">
  <header><span>{fixture.home_team}</span><b>vs</b><span>{fixture.away_team}</span></header>
  <strong>{prediction.label}</strong>
  <small>{prediction.confidence}</small>
  <OutcomeBars fixture={fixture} />
</article>
```

- [ ] **Step 4: Add `MatchOutlook` to the app**

Replace `<FixtureExplorer fixtures={data.fixtures} />` with
`<MatchOutlook fixtures={data.fixtures} />`.

- [ ] **Step 5: Run tests and verify GREEN**

Run: `cd dashboard && npm run test:unit -- components/match-outlook.test.tsx components/dashboard-app.test.tsx`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add dashboard/components/match-outlook.tsx dashboard/components/match-outlook.test.tsx dashboard/components/dashboard-app.tsx dashboard/components/fixture-explorer.tsx
git commit -m "feat: add match winner outlook"
```

### Task 4: Rich title and standings graphics

**Files:**
- Modify: `dashboard/components/championship-race.tsx`
- Modify: `dashboard/components/convergence-chart.tsx`
- Modify: `dashboard/components/standings-panel.tsx`
- Modify: `dashboard/app/globals.css`
- Test: `dashboard/components/dashboard-app.test.tsx`

**Interfaces:**
- Consumes: existing championship, convergence, expected standings, and position rows
- Produces: accessible podium, probability bars, endpoint-labelled convergence chart, enhanced final table

- [ ] **Step 1: Add failing accessible-display assertions**

```tsx
expect(screen.getByRole("heading", { name: /title forecast/i })).toBeVisible();
expect(screen.getByText(/model probability/i)).toBeVisible();
expect(screen.getByRole("table", { name: /possible final table/i })).toBeVisible();
expect(screen.getByText(/expected points/i)).toBeVisible();
```

- [ ] **Step 2: Run and verify RED**

Run: `cd dashboard && npm run test:unit -- components/dashboard-app.test.tsx`

Expected: FAIL on new public headings and accessible table name.

- [ ] **Step 3: Refine the title race**

Render the top three as a podium and all clubs as labelled probability bars.
Keep exact probability text visible outside tooltips. Add CI text in the top
club detail. Use `aria-label` values such as
`"Galatasaray SK title probability 36.1 percent"`.

- [ ] **Step 4: Refine convergence**

Keep the checkpoint chart as evidence that five-million-run estimates
stabilized. Rename it **Model convergence**, remove interactive checkpoint
selection, label final endpoints, and explain the x-axis as cumulative season
paths rather than user simulation progress.

- [ ] **Step 5: Refine standings**

Use the published expected table only. Add:

- sticky rank and club columns;
- current points/GD when non-zero;
- expected position and points;
- most-likely position;
- title, top-four, and relegation probability bars;
- expandable 1st–18th heatmap;
- title/Europe/relegation zone markers;
- responsive mobile cards.

- [ ] **Step 6: Implement visual polish and reduced motion**

Add CSS tokens for probability gradients, podium glow, chart glass panels,
zebra table rows, sticky headers, match cards, focus rings, and:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

- [ ] **Step 7: Run tests, typecheck, and lint**

Run: `cd dashboard && npm run test:unit && npm run typecheck && npm run lint`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add dashboard/components dashboard/app/globals.css
git commit -m "feat: polish forecast charts and standings"
```

### Task 5: Academic methodology and validation narrative

**Files:**
- Modify: `dashboard/components/methodology.tsx`
- Modify: `dashboard/components/backtest-panel.tsx`
- Modify: `dashboard/components/dashboard-app.test.tsx`
- Modify: `README.md`

**Interfaces:**
- Consumes: `DashboardPayload.meta`, `backtest`, `position_backtest`, `freshness`
- Produces: ten-part methodology contract and plain-English validation summary

- [ ] **Step 1: Add failing methodology assertions**

```tsx
for (const heading of [
  "Forecast target", "Data provenance", "Temporal integrity",
  "Structural model", "Market-value adjustment", "Current-season state",
  "Monte Carlo estimation", "Backtest design", "Uncertainty", "Limitations",
]) {
  expect(screen.getByRole("heading", { name: heading })).toBeVisible();
}
```

- [ ] **Step 2: Run and verify RED**

Run: `cd dashboard && npm run test:unit -- components/dashboard-app.test.tsx`

Expected: FAIL because the current methodology is shorter and simulator-focused.

- [ ] **Step 3: Implement the ten methodology sections**

Use semantic `<article>`, `<h3>`, `<p>`, `<ol>`, `<dl>`, and `<code>` elements.
Include the model equations:

```text
λ_home = μ_home × attack_home × defence_away × value_adjustment
λ_away = μ_away × attack_away × defence_home ÷ value_adjustment
```

Explain Poisson score generation, Dixon–Coles low-score correction, completed
match fixing, deterministic five-million-path sampling, tie-break ordering,
proper scoring rules, baselines, and disclosed limitations.

- [ ] **Step 4: Rewrite validation as evidence, not promotion**

Lead with whether the acceptance checks passed. Define log loss, Brier score,
expected-rank error, and rank correlation in plain language. Show the model and
baseline values side by side and avoid unsupported accuracy claims.

- [ ] **Step 5: Rewrite the README**

Put the public URL first, followed by:

- research/non-betting disclaimer;
- current update policy;
- model summary;
- sources and temporal integrity;
- 20-season backtest evidence;
- local commands;
- full verification commands;
- deployment architecture;
- limitations;
- MCT ownership.

- [ ] **Step 6: Run tests and verify GREEN**

Run: `cd dashboard && npm run test:unit -- components/dashboard-app.test.tsx`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add dashboard/components/methodology.tsx dashboard/components/backtest-panel.tsx dashboard/components/dashboard-app.test.tsx README.md
git commit -m "docs: publish forecast methodology and evidence"
```

### Task 6: Daily workflow and production verification

**Files:**
- Modify: `.github/workflows/update-forecast.yml`
- Modify: `.github/workflows/deploy-pages.yml`
- Modify: `tests/workflows/test_github_actions.py`
- Modify: `dashboard/tests/static-build.test.mjs`

**Interfaces:**
- Consumes: validated forecast updater and Vite Pages build
- Produces: one daily update and repository-subpath-safe production deployment

- [ ] **Step 1: Write failing workflow assertions**

```py
assert 'cron: "17 3 * * *"' in update_text
assert "5000000" in update_text
assert "dashboard/public/data/dashboard.json" in update_text
assert "/superlig-forecast/" in deploy_text
```

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest -q tests/workflows/test_github_actions.py`

Expected: FAIL because the updater currently runs every six hours.

- [ ] **Step 3: Change the schedule to daily**

Use `17 3 * * *` (06:17 Europe/Istanbul during UTC+3) and preserve manual
dispatch. Keep the five-million run, source reconciliation, quality gates,
atomic data commit, and concurrent-push retry.

- [ ] **Step 4: Verify the Pages base**

Keep `VITE_BASE_PATH=/superlig-forecast/`. Extend the static-build test to assert
that bundled links and worker-free assets resolve under the repository subpath.

- [ ] **Step 5: Run complete local verification**

Run:

```bash
uv run pytest -q --cov=superlig_forecast --cov-report=term-missing:skip-covered
uv run mypy src
uv run ruff check src tests
uv run ruff format --check src tests
cd dashboard
npm test
npm run typecheck
npm run lint
npm run build:pages
npm audit --omit=dev
```

Expected: all commands exit 0; production audit reports zero high and critical
vulnerabilities.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows tests/workflows dashboard/tests
git commit -m "ci: publish the daily forecast brief"
```

### Task 7: Publish repository and add MCT portfolio entry

**Files:**
- Modify in governance repository: `portfolio/repositories.json`
- Modify in governance repository: `portfolio/products.json`
- Modify in governance repository: `portfolio/logo-inventory.json`
- Modify in governance repository: `brand/lockups.md`
- Copy in governance repository: `assets/logos/superlig-forecast.png`
- Modify in website repository: `src/content/site.json`
- Copy in website repository: `src/assets/products/superlig-forecast-logo.png`
- Modify in website repository: `tests/homepage-content.test.mjs`
- Modify in website repository: `README.md`

**Interfaces:**
- Consumes: verified forecast branch and `dashboard/public/brand/mct-icon.png`
- Produces: public GitHub repository, Pages URL, and monarchcastle.tech product card

- [ ] **Step 1: Create and push the authorized public repository**

```bash
gh repo create MonarchCastleTech/superlig-forecast \
  --public \
  --description "Daily probabilistic 2026–27 Süper Lig title, table, and match-outcome forecast by Monarch Castle Technologies." \
  --source . \
  --remote origin
git branch -M main
git push -u origin main
```

Expected: repository exists at
`https://github.com/MonarchCastleTech/superlig-forecast`.

- [ ] **Step 2: Enable Pages through Actions and dispatch deployment**

```bash
gh api --method POST repos/MonarchCastleTech/superlig-forecast/pages \
  -f build_type=workflow
gh workflow run deploy-pages.yml --repo MonarchCastleTech/superlig-forecast
gh run watch --repo MonarchCastleTech/superlig-forecast --exit-status
```

If Pages already exists, use `PUT` instead of treating HTTP 409 as a failure.

- [ ] **Step 3: Add a failing governance registry test**

First register the new repository and product in
`MonarchCastleTech/company-governance`, because the public website is an exact
projection of that private source of truth. Add a failing governance test that
expects repository `MonarchCastleTech/superlig-forecast`, product
`superlig-forecast`, its product-specific logo inventory record, and a
`Süper Lig Forecast` section in `brand/lockups.md` containing the canonical MCT
endorsement.

Run: `npm test`

Expected: FAIL because the governed records do not exist.

- [ ] **Step 4: Update and publish the governance source of truth**

Add the repository record, product record, approved logo inventory record, logo
bytes, and lockup text. Use family `forecasting-intelligence`, lifecycle
`production`, daily update frequency, forecast capability
`probabilistic-season-and-match-outcome-forecast`, and evidence status
`20-season-expanding-window-backtest; daily-source-gated-release`.

Run:

```bash
npm test
git add portfolio assets/logos/superlig-forecast.png brand/lockups.md tests
git commit -m "feat: register Süper Lig Forecast"
git push origin main
```

Expected: governance tests pass and the source-of-truth commit is published.

- [ ] **Step 5: Add a failing website registry test**

```js
assert.match(homepage, /Süper Lig Forecast/);
assert.match(homepage, /Daily/);
assert.match(homepage, /superlig-forecast/);
```

Run: `npm test`

Expected: FAIL because the product is not registered.

- [ ] **Step 6: Sync the governed product entry**

Run the website content sync against the adjacent governance checkout. The
projected product contains:

```json
{
  "id": "superlig-forecast",
  "name": "Süper Lig Forecast",
  "family": "forecasting-intelligence",
  "lifecycle": "production",
  "regions": ["Türkiye"],
  "methodologyUrl": "https://github.com/MonarchCastleTech/superlig-forecast#methodology",
  "updateFrequency": "daily",
  "canonicalUrl": "https://monarchcastletech.github.io/superlig-forecast/",
  "owner": "MonarchCastleTech",
  "forecastEvidenceStatus": "20-season expanding-window backtest; daily source-gated forecast",
  "endorsementLabel": "Part of Monarch Castle Technologies"
}
```

Set `logo` to an `approved-image` object with the governed copied asset path,
computed SHA-256, and alt text `Süper Lig Forecast product mark`.

- [ ] **Step 7: Verify and push the MCT website**

Run:

```bash
npm ci
npm run verify
git add src/content/site.json src/assets/products/superlig-forecast-logo.png tests/homepage-content.test.mjs README.md
git commit -m "feat: add Süper Lig Forecast to portfolio"
git push origin main
gh run watch --repo MonarchCastleTech/MonarchCastleTech.github.io --exit-status
```

Expected: website tests and Pages workflow pass.

- [ ] **Step 8: Verify both live URLs**

Run:

```bash
node scripts/check-live-site.mjs
```

Also verify HTTP 200 and visible product content at:

- `https://monarchcastletech.github.io/superlig-forecast/`
- `https://monarchcastle.tech/`

- [ ] **Step 9: Record final release URLs**

Report the source repository, dashboard URL, company portfolio URL, update
schedule, test totals, and any deployment propagation delay.
