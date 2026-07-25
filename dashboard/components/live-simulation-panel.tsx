import { useMemo, useState } from "react";
import { LiveProbabilityChart } from "@/components/live-probability-chart";
import type { LiveSimulationController } from "@/hooks/use-live-simulation";
import {
  formatInteger,
  type DashboardPayload,
  type ExpectedStanding,
  type PositionRow,
} from "@/lib/dashboard-data";
import type { SimulationSnapshot } from "@/lib/live-simulation";

type LiveSimulationPanelProps = {
  data: DashboardPayload;
  controller: LiveSimulationController;
};

function ordinal(position: number): string {
  const remainder = position % 100;
  if (remainder >= 11 && remainder <= 13) return `${position}th`;
  if (position % 10 === 1) return `${position}st`;
  if (position % 10 === 2) return `${position}nd`;
  if (position % 10 === 3) return `${position}rd`;
  return `${position}th`;
}

function medianPosition(counts: number[], simulations: number): number {
  let cumulative = 0;
  for (let index = 0; index < counts.length; index += 1) {
    cumulative += counts[index];
    if (cumulative >= simulations / 2) return index + 1;
  }
  return counts.length;
}

// Shared with the dashboard shell so one live snapshot drives both views.
// eslint-disable-next-line react-refresh/only-export-components
export function deriveLiveTables(
  snapshot: SimulationSnapshot,
): {
  positionRows: PositionRow[];
  expectedStandings: ExpectedStanding[];
} {
  const simulations = snapshot.simulations;
  const teamCount = snapshot.teams.length;
  const positionRows = snapshot.teams.flatMap((team) =>
    team.positionCounts.map((count, index) => ({
      club: team.club,
      position: index + 1,
      count,
      probability: simulations > 0 ? count / simulations : 0,
    })),
  );
  const expectedStandings = snapshot.teams
    .map((team) => {
      const probabilities = team.positionCounts.map((count) =>
        simulations > 0 ? count / simulations : 0,
      );
      let mostLikely = 0;
      for (let index = 1; index < probabilities.length; index += 1) {
        if (probabilities[index] > probabilities[mostLikely]) {
          mostLikely = index;
        }
      }
      return {
        club: team.club,
        expected_position: probabilities.reduce(
          (sum, probability, index) => sum + probability * (index + 1),
          0,
        ),
        median_position: medianPosition(team.positionCounts, simulations),
        most_likely_position: mostLikely + 1,
        expected_points:
          simulations > 0 ? team.pointSum / simulations : 0,
        expected_goal_difference:
          simulations > 0 ? team.goalDifferenceSum / simulations : 0,
        top_four_probability: probabilities
          .slice(0, Math.min(4, teamCount))
          .reduce((sum, value) => sum + value, 0),
        position_17_probability:
          teamCount >= 17 ? probabilities[16] : null,
        relegation_probability: probabilities
          .slice(Math.max(0, teamCount - 3))
          .reduce((sum, value) => sum + value, 0),
      };
    })
    .sort(
      (left, right) =>
        left.expected_position - right.expected_position ||
        left.club.localeCompare(right.club),
    );
  return { positionRows, expectedStandings };
}

function randomSeed(): number {
  if (typeof crypto !== "undefined" && crypto.getRandomValues) {
    return crypto.getRandomValues(new Uint32Array(1))[0] || 1;
  }
  return (Date.now() >>> 0) || 1;
}

export function LiveSimulationPanel({
  data,
  controller,
}: LiveSimulationPanelProps) {
  const [target, setTarget] = useState(100_000);
  const [infinite, setInfinite] = useState(false);
  const [seed, setSeed] = useState(data.meta.seed);
  const [selectedPosition, setSelectedPosition] = useState(1);
  const [visibleClubs, setVisibleClubs] = useState<Set<string>>(
    () =>
      new Set(
        data.championship.slice(0, 6).map((row) => row.club),
      ),
  );
  const snapshot = controller.snapshot;
  const simulations = snapshot?.simulations ?? 0;
  const elapsedMs = snapshot?.elapsedMs ?? 0;
  const simulationsPerSecond =
    elapsedMs > 0 ? simulations / (elapsedMs / 1_000) : 0;
  const progress = infinite
    ? null
    : Math.min(1, simulations / Math.max(1, target));
  const finiteTargetValid =
    Number.isSafeInteger(target) && target > 0;
  const playDisabled =
    controller.status === "running" ||
    controller.status === "paused" ||
    (!infinite && !finiteTargetValid);
  const clubNames = useMemo(
    () => data.championship.map((row) => row.club),
    [data.championship],
  );

  function toggleClub(club: string) {
    setVisibleClubs((current) => {
      const next = new Set(current);
      if (next.has(club) && next.size > 1) next.delete(club);
      else next.add(club);
      return next;
    });
  }

  function play() {
    if (!infinite && !finiteTargetValid) return;
    controller.start(
      infinite
        ? { infinite: true, target: null }
        : { infinite: false, target },
      seed,
    );
  }

  return (
    <section className="panel live-simulation-panel" aria-labelledby="live-heading">
      <div className="panel-heading">
        <div>
          <p className="section-index">01 / live simulator</p>
          <h2 id="live-heading">Play the season millions of times</h2>
        </div>
        <span className={`runner-state state-${controller.status}`}>
          {controller.status}
        </span>
      </div>

      <div className="simulation-controls">
        <label>
          <span>Simulation target</span>
          <input
            aria-label="Simulation target"
            disabled={infinite}
            max={Number.MAX_SAFE_INTEGER}
            min={1}
            onChange={(event) => setTarget(Number(event.target.value))}
            step={1}
            type="number"
            value={target}
          />
        </label>
        <label className="check-control">
          <input
            checked={infinite}
            name="infinite"
            onChange={(event) => setInfinite(event.target.checked)}
            type="checkbox"
          />
          <span>Run until stopped</span>
        </label>
        <label>
          <span>Seed</span>
          <input
            aria-label="Simulation seed"
            min={0}
            onChange={(event) => setSeed(Number(event.target.value) >>> 0)}
            step={1}
            type="number"
            value={seed}
          />
        </label>
        <button onClick={() => setSeed(randomSeed())} type="button">
          New seed
        </button>
        <label>
          <span>Exact finishing position</span>
          <select
            aria-label="Exact finishing position"
            onChange={(event) =>
              setSelectedPosition(Number(event.target.value))
            }
            value={selectedPosition}
          >
            {Array.from(
              { length: data.meta.team_count },
              (_, index) => index + 1,
            ).map((position) => (
              <option key={position} value={position}>
                {ordinal(position)}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="transport-controls">
        <button
          disabled={playDisabled}
          onClick={play}
          type="button"
          aria-label="Play simulation"
        >
          Play
        </button>
        <button
          disabled={controller.status !== "running"}
          onClick={controller.pause}
          type="button"
        >
          Pause
        </button>
        <button
          disabled={controller.status !== "paused"}
          onClick={controller.resume}
          type="button"
        >
          Resume
        </button>
        <button
          disabled={
            controller.status !== "running" &&
            controller.status !== "paused"
          }
          onClick={controller.stop}
          type="button"
        >
          Stop
        </button>
        <button
          disabled={controller.status === "idle" && !snapshot}
          onClick={controller.reset}
          type="button"
        >
          Reset
        </button>
      </div>

      <div className="live-scoreboard" aria-live="polite">
        <article>
          <span>Completed</span>
          <strong>{formatInteger(simulations)}</strong>
        </article>
        <article>
          <span>Seasons / second</span>
          <strong>{formatInteger(Math.round(simulationsPerSecond))}</strong>
        </article>
        <article>
          <span>Elapsed</span>
          <strong>{(elapsedMs / 1_000).toFixed(1)}s</strong>
        </article>
        <article>
          <span>Progress</span>
          <strong>
            {progress === null ? "∞" : `${(progress * 100).toFixed(1)}%`}
          </strong>
        </article>
      </div>
      {progress !== null ? (
        <progress
          aria-label="Simulation progress"
          max={1}
          value={progress}
        />
      ) : null}
      {controller.error ? (
        <p className="simulation-error" role="alert">
          {controller.error}
        </p>
      ) : null}

      <LiveProbabilityChart
        history={controller.history}
        selectedPosition={selectedPosition}
        visibleClubs={visibleClubs}
      />

      <div className="club-toggles compact" aria-label="Live chart clubs">
        {clubNames.map((club) => (
          <button
            aria-pressed={visibleClubs.has(club)}
            key={club}
            onClick={() => toggleClub(club)}
            type="button"
          >
            {club}
          </button>
        ))}
      </div>
    </section>
  );
}
