# Live Monte Carlo Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the predetermined-first dashboard experience with a responsive sports-style Monte Carlo player that accepts finite or infinite runs, streams exact-position probabilities, and carries official MCT branding.

**Architecture:** Convert the dashboard to a static Vite React application suitable for GitHub Pages. Run deterministic season simulations in a dedicated Web Worker, stream compact cumulative snapshots to React, and derive the live graph and table from authoritative position counts.

**Tech Stack:** React 19, TypeScript, Vite, Recharts, Web Workers, Vitest, Testing Library, CSS.

## Global Constraints

- The application remains a forecast-quality research tool, not a betting product.
- Finite mode accepts any positive safe integer; infinite mode runs until Pause, Stop, or Reset.
- Every exact position from 1 through the current team count is selectable.
- The checked-in five-million-run forecast remains available only as a clearly labelled reference.
- The official MCT logo must come from an MCT-controlled repository, be stored locally, and never be recreated.
- Static output must work at `/` and at a GitHub repository subpath.
- Simulation counts are cumulative integers and must remain authoritative when chart history is compacted.
- Implement every behavior test-first and commit after each task.

---

### Task 1: Convert the dashboard to a static Vite application

**Files:**
- Create: `dashboard/index.html`
- Create: `dashboard/src/main.tsx`
- Create: `dashboard/src/app-loader.tsx`
- Create: `dashboard/tests/static-build.test.mjs`
- Modify: `dashboard/package.json`
- Modify: `dashboard/vite.config.ts`
- Modify: `dashboard/tsconfig.json`
- Modify: `dashboard/eslint.config.mjs`
- Modify: `run-dashboard.ps1`
- Delete: `dashboard/app/layout.tsx`
- Delete: `dashboard/app/page.tsx`
- Delete: `dashboard/worker/index.ts`
- Delete: `dashboard/build/sites-vite-plugin.ts`
- Delete: `dashboard/tests/rendered-html.test.mjs`

**Interfaces:**
- Consumes: `validateDashboardPayload(value: unknown): DashboardPayload` from `dashboard/lib/dashboard-data.ts`.
- Produces: a static entry at `dashboard/dist/index.html` and a runtime loader that fetches `${import.meta.env.BASE_URL}data/dashboard.json`.

- [ ] **Step 1: Write the failing static-build contract**

Create `dashboard/tests/static-build.test.mjs`:

```js
import assert from "node:assert/strict";
import { readFile, readdir } from "node:fs/promises";
import test from "node:test";

test("builds a repository-subpath-safe static dashboard", async () => {
  const html = await readFile(new URL("../dist/index.html", import.meta.url), "utf8");
  const assets = await readdir(new URL("../dist/assets/", import.meta.url));

  assert.match(html, /<div id="root"><\/div>/);
  assert.match(html, /\/superlig-forecast\/assets\//);
  assert.ok(assets.some((name) => name.endsWith(".js")));
  assert.ok(assets.some((name) => name.endsWith(".css")));
  await readFile(new URL("../dist/data/dashboard.json", import.meta.url));
});
```

- [ ] **Step 2: Run the new contract to verify RED**

Run:

```powershell
cd dashboard
npm run build:pages
node --test tests/static-build.test.mjs
```

Expected: FAIL because `build:pages`, the static entry, or repository-base assets do not exist.

- [ ] **Step 3: Add the static entry and loader**

Create `dashboard/index.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="theme-color" content="#0a0d0b" />
    <title>Süper Lig Forecast Lab</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Create `dashboard/src/app-loader.tsx`:

```tsx
import { useEffect, useState } from "react";
import { DashboardApp } from "@/components/dashboard-app";
import {
  type DashboardPayload,
  validateDashboardPayload,
} from "@/lib/dashboard-data";

export function AppLoader() {
  const [data, setData] = useState<DashboardPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const url = `${import.meta.env.BASE_URL}data/dashboard.json`;
    fetch(url)
      .then((response) => {
        if (!response.ok) throw new Error(`Dashboard data returned ${response.status}`);
        return response.json();
      })
      .then((value) => setData(validateDashboardPayload(value)))
      .catch((reason: unknown) =>
        setError(reason instanceof Error ? reason.message : "Dashboard data failed to load"),
      );
  }, []);

  if (error) return <main className="load-state" role="alert">{error}</main>;
  if (!data) return <main className="load-state">Loading forecast data…</main>;
  return <DashboardApp data={data} />;
}
```

Create `dashboard/src/main.tsx`:

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { AppLoader } from "./app-loader";
import "../app/globals.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <AppLoader />
  </StrictMode>,
);
```

- [ ] **Step 4: Replace the Vinext/Cloudflare configuration with Vite React**

Set `dashboard/vite.config.ts` to:

```ts
import { fileURLToPath, URL } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  base: process.env.VITE_BASE_PATH || "/",
  plugins: [react()],
  resolve: {
    alias: { "@": fileURLToPath(new URL(".", import.meta.url)) },
  },
});
```

Update `dashboard/package.json` scripts to:

```json
{
  "dev": "vite",
  "build": "vite build",
  "build:pages": "cross-env VITE_BASE_PATH=/superlig-forecast/ vite build",
  "preview": "vite preview",
  "test": "vitest run --config vitest.config.ts && npm run build:pages && node --test tests/static-build.test.mjs",
  "test:unit": "vitest run --config vitest.config.ts",
  "typecheck": "tsc --noEmit",
  "lint": "eslint . --ignore-pattern dist"
}
```

Keep the existing `@vitejs/plugin-react`; add `@testing-library/react`,
`@testing-library/user-event`, `jsdom`, `typescript-eslint`,
`eslint-plugin-react-hooks`, and `eslint-plugin-react-refresh`. Remove `next`,
`vinext`, `@cloudflare/vite-plugin`, `@cloudflare/workers-types`,
`@vitejs/plugin-rsc`, `eslint-config-next`, `react-server-dom-webpack`, and
`wrangler`. Replace the Next-specific ESLint configuration with the standard
TypeScript, React Hooks, and React Refresh flat configs. Retain Tailwind/PostCSS
because `globals.css` imports `tailwindcss`. Update `run-dashboard.ps1` only if
the standard Vite command or printed URL changes.

- [ ] **Step 5: Run the static contract and dashboard checks**

Run:

```powershell
cd dashboard
npm install
npm test
npm run typecheck
npm run lint
```

Expected: all commands PASS and `dist/index.html` references
`/superlig-forecast/assets/`.

- [ ] **Step 6: Commit the static foundation**

```powershell
git add dashboard run-dashboard.ps1
git commit -m "refactor: make forecast dashboard a static vite app"
```

---

### Task 2: Implement the deterministic season simulation core

**Files:**
- Create: `dashboard/lib/live-simulation.ts`
- Create: `dashboard/lib/live-simulation.test.ts`

**Interfaces:**
- Consumes: `FixtureRow` from `dashboard/lib/dashboard-data.ts`.
- Produces:
  - `prepareFixtures(teams: string[], fixtures: FixtureRow[]): IndexedFixture[]`
  - `createAccumulator(teamCount: number, seed: number): SimulationAccumulator`
  - `simulateBatch(state, fixtures, count): SimulationAccumulator`
  - `toSnapshot(state, teams, elapsedMs): SimulationSnapshot`

- [ ] **Step 1: Write failing deterministic and invariant tests**

Create tests containing:

```ts
import { describe, expect, test } from "vitest";
import {
  createAccumulator,
  prepareFixtures,
  simulateBatch,
  toSnapshot,
} from "./live-simulation";

const teams = ["A", "B", "C"];
const fixtures = prepareFixtures(teams, [
  {
    home_team: "A",
    away_team: "B",
    home_expected_goals: 1.5,
    away_expected_goals: 0.8,
    home_win_probability: 0.54,
    draw_probability: 0.27,
    away_win_probability: 0.19,
  },
  {
    home_team: "B",
    away_team: "C",
    home_expected_goals: 1.1,
    away_expected_goals: 1.0,
    home_win_probability: 0.39,
    draw_probability: 0.31,
    away_win_probability: 0.30,
  },
]);

test("reproduces a seeded run across batch boundaries", () => {
  const oneBatch = simulateBatch(createAccumulator(3, 42), fixtures, 200);
  const split = simulateBatch(
    simulateBatch(createAccumulator(3, 42), fixtures, 75),
    fixtures,
    125,
  );
  expect(toSnapshot(split, teams, 1)).toEqual(toSnapshot(oneBatch, teams, 1));
});

test("assigns every team to exactly one position per season", () => {
  const snapshot = toSnapshot(
    simulateBatch(createAccumulator(3, 7), fixtures, 100),
    teams,
    10,
  );
  for (const team of snapshot.teams) {
    expect(team.positionCounts.reduce((sum, value) => sum + value, 0)).toBe(100);
  }
  for (let position = 0; position < 3; position += 1) {
    expect(snapshot.teams.reduce(
      (sum, team) => sum + team.positionCounts[position],
      0,
    )).toBe(100);
  }
});
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
cd dashboard
npx vitest run lib/live-simulation.test.ts
```

Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement the minimal seeded simulator**

Implement these exact public types:

```ts
export type IndexedFixture = {
  home: number;
  away: number;
  homeExpectedGoals: number;
  awayExpectedGoals: number;
};

export type TeamSimulationSnapshot = {
  club: string;
  positionCounts: number[];
  pointSum: number;
  goalDifferenceSum: number;
};

export type SimulationSnapshot = {
  simulations: number;
  elapsedMs: number;
  teams: TeamSimulationSnapshot[];
};

export type SimulationAccumulator = {
  simulations: number;
  rngState: number;
  positionCounts: Float64Array;
  pointSums: Float64Array;
  goalDifferenceSums: Float64Array;
};
```

Use a stateful xorshift32 generator and Knuth Poisson sampling. Rank on points,
goal difference, goals scored, then team index. Clone typed arrays when returning
state so tests and worker snapshots cannot observe partially mutated batches.

- [ ] **Step 4: Run the simulation tests to verify GREEN**

Run:

```powershell
cd dashboard
npx vitest run lib/live-simulation.test.ts
```

Expected: PASS with both tests green.

- [ ] **Step 5: Add null-xG and safe-integer tests**

Add tests proving `prepareFixtures` rejects missing expected goals and
`simulateBatch` rejects a count that would exceed `Number.MAX_SAFE_INTEGER`.
Implement the explicit error messages:

```ts
"Live simulation requires expected goals for every fixture"
"Simulation count exceeds JavaScript safe integer range"
```

- [ ] **Step 6: Run all unit tests and commit**

```powershell
cd dashboard
npm run test:unit
cd ..
git add dashboard/lib/live-simulation.ts dashboard/lib/live-simulation.test.ts
git commit -m "feat: add deterministic browser season simulator"
```

---

### Task 3: Add the worker protocol and finite/infinite runner

**Files:**
- Create: `dashboard/lib/live-worker-protocol.ts`
- Create: `dashboard/lib/live-worker-protocol.test.ts`
- Create: `dashboard/workers/season-simulator.worker.ts`
- Create: `dashboard/hooks/use-live-simulation.ts`

**Interfaces:**
- Consumes: simulation functions and types from Task 2.
- Produces:
  - `WorkerCommand = StartCommand | PauseCommand | ResumeCommand | StopCommand | ResetCommand`
  - `WorkerEvent = ProgressEvent | StateEvent | ErrorEvent`
  - `useLiveSimulation(data: DashboardPayload): LiveSimulationController`

- [ ] **Step 1: Write failing protocol/state tests**

Test the public runner state:

```ts
test("finite runs stop exactly at the requested target", () => {
  expect(nextBatchSize({ simulations: 990, target: 1_000, infinite: false })).toBe(10);
});

test("infinite runs always schedule another bounded batch", () => {
  expect(nextBatchSize({ simulations: 5_000_000, target: null, infinite: true }))
    .toBeGreaterThan(0);
});

test("ignores progress from a stale run id", () => {
  const current = initialRunnerState("run-2");
  expect(reduceWorkerEvent(current, progressEvent("run-1"))).toEqual(current);
});
```

- [ ] **Step 2: Run the protocol tests to verify RED**

Run `npx vitest run lib/live-worker-protocol.test.ts`.

Expected: FAIL because the protocol module does not exist.

- [ ] **Step 3: Implement protocol helpers**

Use:

```ts
export type RunMode = { infinite: true; target: null } |
  { infinite: false; target: number };
export type RunnerStatus = "idle" | "running" | "paused" | "stopped" | "complete" | "error";
```

`nextBatchSize` must return 25 below 250 simulations, 250 below 10,000,
2,500 below 250,000, and 10,000 afterward, capped to a finite target.

- [ ] **Step 4: Implement the yielding Web Worker**

The worker must run one batch per macrotask:

```ts
function schedule() {
  if (status !== "running") return;
  setTimeout(runNextBatch, 0);
}
```

Post progress no more often than every 100 ms, plus a final snapshot. Process
Pause, Resume, Stop, and Reset only between batches. Every message includes
`runId`.

- [ ] **Step 5: Implement `useLiveSimulation`**

Construct the worker with:

```ts
new Worker(
  new URL("../workers/season-simulator.worker.ts", import.meta.url),
  { type: "module" },
);
```

Expose:

```ts
type LiveSimulationController = {
  status: RunnerStatus;
  snapshot: SimulationSnapshot | null;
  history: SimulationSnapshot[];
  error: string | null;
  start: (mode: RunMode, seed: number) => void;
  pause: () => void;
  resume: () => void;
  stop: () => void;
  reset: () => void;
};
```

Compact history to at most 600 points while always preserving the first and
newest snapshots.

- [ ] **Step 6: Run protocol tests, type checking, and commit**

```powershell
cd dashboard
npx vitest run lib/live-worker-protocol.test.ts
npm run typecheck
cd ..
git add dashboard/lib/live-worker-protocol* dashboard/workers dashboard/hooks
git commit -m "feat: stream finite and infinite simulations from a worker"
```

---

### Task 4: Build the live scoreboard, graph, and evolving table

**Files:**
- Create: `dashboard/components/live-simulation-panel.tsx`
- Create: `dashboard/components/live-probability-chart.tsx`
- Create: `dashboard/components/live-simulation-panel.test.tsx`
- Modify: `dashboard/components/dashboard-app.tsx`
- Modify: `dashboard/components/standings-panel.tsx`
- Modify: `dashboard/components/convergence-chart.tsx`
- Modify: `dashboard/vitest.config.ts`

**Interfaces:**
- Consumes: `useLiveSimulation`, `SimulationSnapshot`, and `DashboardPayload`.
- Produces: primary live controls and live-derived `PositionRow[]` /
  `ExpectedStanding[]` views.

- [ ] **Step 1: Configure jsdom and write the failing control test**

The test must render the panel with a fake controller and assert:

```tsx
expect(screen.getByLabelText("Simulation target")).toHaveValue(100000);
await user.click(screen.getByRole("checkbox", { name: "Run until stopped" }));
expect(screen.getByLabelText("Simulation target")).toBeDisabled();
await user.click(screen.getByRole("button", { name: "Play simulation" }));
expect(controller.start).toHaveBeenCalledWith(
  { infinite: true, target: null },
  expect.any(Number),
);
```

- [ ] **Step 2: Run the component test to verify RED**

Run `npx vitest run components/live-simulation-panel.test.tsx`.

Expected: FAIL because the component does not exist.

- [ ] **Step 3: Implement the live controls and scoreboard**

The panel must include:

- target number input;
- infinite checkbox;
- numeric seed input and “new seed” button;
- Play/Pause/Resume/Stop/Reset buttons with state-appropriate disabling;
- completed simulations, simulations/second, elapsed time, and progress;
- selected exact-position dropdown from 1 through `data.meta.team_count`.

Use native labels and buttons; announce status changes through
`aria-live="polite"`.

- [ ] **Step 4: Implement live chart derivation**

For each history snapshot, calculate:

```ts
probability = team.positionCounts[selectedPosition - 1] / snapshot.simulations;
```

Render visible clubs as Recharts `Line` series. The x-axis is cumulative
simulations on a logarithmic scale after 100 runs. The chart title must read
`Live probability · exact Nth place`, not “forecast certainty.”

- [ ] **Step 5: Feed live positions into the standings panel**

Refactor `StandingsPanel` to accept:

```ts
type StandingsPanelProps = {
  data: DashboardPayload;
  positionRows?: PositionRow[];
  expectedStandings?: ExpectedStanding[];
  sourceLabel?: string;
};
```

When a live snapshot exists, derive counts, probabilities, expected position,
expected points, and expected goal difference. Title the section
`Live possible standings`. When no run exists, render the published table as
`Reference possible standings`.

- [ ] **Step 6: Demote predetermined checkpoints**

Keep the existing convergence chart below the live player and rename it
`Published reference convergence`. Remove the checkpoint strip as the primary
interaction. It may remain inside the reference section for auditability.

- [ ] **Step 7: Run component and integration tests, then commit**

```powershell
cd dashboard
npx vitest run components/live-simulation-panel.test.tsx
npm test
npm run typecheck
cd ..
git add dashboard/components dashboard/vitest.config.ts
git commit -m "feat: add live probability player and evolving table"
```

---

### Task 5: Apply sports styling and official MCT branding

**Files:**
- Create: `scripts/import_mct_logo.py`
- Create: `tests/scripts/test_import_mct_logo.py`
- Generate: `dashboard/public/brand/mct-icon.png`
- Modify: `dashboard/components/dashboard-app.tsx`
- Modify: `dashboard/app/globals.css`
- Modify: `dashboard/tests/static-build.test.mjs`

**Interfaces:**
- Consumes: official asset
  `https://raw.githubusercontent.com/MonarchCastleTech/.github/main/profile/icon.png`
  with Git blob SHA `9207bb10f49b0f0958adbf51b2c0d89a965f7484`.
- Produces: local `/brand/mct-icon.png`, masthead/footer branding, sports scoreboard classes.

- [ ] **Step 1: Write the failing asset-import test**

Test the Git blob verifier without network:

```py
from scripts.import_mct_logo import git_blob_sha

def test_git_blob_sha_matches_git_object_format() -> None:
    assert git_blob_sha(b"test content\n") == "d670460b4b4aece5915caf5c68d12f560a9fe3e4"
```

- [ ] **Step 2: Run the test to verify RED**

Run `uv run pytest tests/scripts/test_import_mct_logo.py -q`.

Expected: FAIL because the importer does not exist.

- [ ] **Step 3: Implement and run the pinned importer**

Implement:

```py
def git_blob_sha(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode()
    return hashlib.sha1(header + content, usedforsecurity=False).hexdigest()
```

The script downloads with `httpx`, requires the expected Git blob SHA, and
writes only `dashboard/public/brand/mct-icon.png`. Run it once and commit the
resulting official binary.

- [ ] **Step 4: Add branding tests before markup**

Extend `static-build.test.mjs` to require the local brand asset. Add a component
test requiring two images with alt text `Monarch Castle Technologies`.

Run tests and verify RED because the images are absent.

- [ ] **Step 5: Add masthead and footer branding**

Use `${import.meta.env.BASE_URL}brand/mct-icon.png`, preserve aspect ratio, and
link to `https://github.com/MonarchCastleTech`. Add the descriptor
`Forecasting Intelligence`.

- [ ] **Step 6: Implement the sports-broadcast visual system**

Add CSS for:

- a compact live scoreboard strip;
- running/paused/stopped status lamps;
- tabular counters and timer typography;
- pitch-grid background texture using CSS gradients only;
- prominent Play and Stop controls;
- responsive control stacking below 760 px;
- `prefers-reduced-motion` removal of pulsing and line transitions.

Retain the existing dark canvas, lime probability accent, coral risk accent,
and WCAG-readable text contrast.

- [ ] **Step 7: Run branding, visual-contract, and full dashboard tests**

```powershell
uv run pytest tests/scripts/test_import_mct_logo.py -q
cd dashboard
npm test
npm run typecheck
npm run lint
cd ..
git add scripts tests/scripts dashboard
git commit -m "feat: apply MCT sports intelligence branding"
```

---

### Task 6: Verify long-running behavior and document operation

**Files:**
- Modify: `dashboard/tests/static-build.test.mjs`
- Modify: `README.md`
- Modify: `TODO.md`

**Interfaces:**
- Consumes: completed live dashboard.
- Produces: verified local runbook and Pages-ready artifact contract.

- [ ] **Step 1: Add an infinite-run smoke contract**

Add a worker test that runs several yielded batches, pauses, confirms the count
does not change, resumes, stops, and confirms no later progress event is
accepted for the stopped run.

- [ ] **Step 2: Add the local runbook**

Document:

```powershell
.\run-dashboard.ps1
```

Then describe finite target entry, infinite mode, seed reproduction, and the
difference between live and published reference results.

- [ ] **Step 3: Run complete frontend verification**

```powershell
cd dashboard
npm test
npm run typecheck
npm run lint
npm audit --omit=dev
```

Expected: tests/build/typecheck/lint PASS and production dependency audit has
zero high or critical vulnerabilities.

- [ ] **Step 4: Verify local HTTP and responsive interaction**

Start `.\run-dashboard.ps1`, open `http://localhost:3000`, and verify:

- finite run completes at the exact requested count;
- infinite run continues until Stop;
- Pause/Resume preserves cumulative counts;
- each exact-position selector changes the live graph;
- the live table changes as batches arrive;
- the MCT logo appears in masthead and footer;
- controls remain usable at 390 px width.

- [ ] **Step 5: Commit documentation**

```powershell
git add README.md TODO.md dashboard/tests
git commit -m "docs: explain live forecast simulation controls"
```
