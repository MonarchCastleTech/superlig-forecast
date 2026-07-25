"use client";

import { useMemo, useState } from "react";

import {
  formatProbability,
  type DashboardPayload,
  type ExpectedStanding,
  type PositionRow,
} from "@/lib/dashboard-data";

type StandingsPanelProps = {
  data: DashboardPayload;
  positionRows?: PositionRow[];
  expectedStandings?: ExpectedStanding[];
  sourceLabel?: string;
};

function ordinal(position: number): string {
  const remainder = position % 100;
  if (remainder >= 11 && remainder <= 13) return `${position}th`;
  if (position % 10 === 1) return `${position}st`;
  if (position % 10 === 2) return `${position}nd`;
  if (position % 10 === 3) return `${position}rd`;
  return `${position}th`;
}

function metric(
  aggregate: Record<string, number>,
  key: string,
): number {
  return aggregate[key] ?? Number.NaN;
}

function leaderAt(
  positions: PositionRow[],
  position: number,
): PositionRow | null {
  return (
    positions
      .filter((row) => row.position === position)
      .sort(
        (left, right) =>
          right.probability - left.probability ||
          left.club.localeCompare(right.club),
      )[0] ?? null
  );
}

export function StandingsPanel({
  data,
  positionRows,
  expectedStandings,
  sourceLabel = "Reference possible standings",
}: StandingsPanelProps) {
  const positions = positionRows ?? data.positions;
  const standings = expectedStandings ?? data.expected_standings;
  const initialLeader = leaderAt(positions, 1);
  const [focusPosition, setFocusPosition] = useState(1);
  const [selectedClub, setSelectedClub] = useState(
    initialLeader?.club ?? standings[0]?.club ?? "",
  );
  const leader = useMemo(
    () => leaderAt(positions, focusPosition),
    [focusPosition, positions],
  );
  const selectedDistribution = useMemo(
    () =>
      positions
        .filter((row) => row.club === selectedClub)
        .sort((left, right) => left.position - right.position),
    [positions, selectedClub],
  );
  const positionMap = useMemo(() => {
    return new Map(
      positions.map((row) => [`${row.club}:${row.position}`, row]),
    );
  }, [positions]);
  const positionScores = data.position_backtest.aggregate;
  const positionLogLoss = metric(positionScores, "position_log_loss");
  const uniformLogLoss = metric(positionScores, "uniform_log_loss");
  const positionMae = metric(
    positionScores,
    "mean_absolute_position_error",
  );
  const uniformMae = metric(
    positionScores,
    "uniform_mean_absolute_position_error",
  );

  return (
    <section className="standings-section" id="standings">
      <div className="section-heading">
        <div>
          <p className="section-index">03 / full table</p>
          <h2>{sourceLabel}</h2>
        </div>
        <p>
          The table is ordered by each club&apos;s average finishing position.
          Open a row to inspect its full exact-position distribution.
        </p>
      </div>

      <div className="position-callout">
        <label>
          <span>Who is most likely to finish</span>
          <select
            aria-label="Position to inspect"
            onChange={(event) => setFocusPosition(Number(event.target.value))}
            value={focusPosition}
          >
            {Array.from({ length: data.meta.team_count }, (_, index) => index + 1).map(
              (position) => (
                <option key={position} value={position}>
                  {ordinal(position)}
                </option>
              ),
            )}
          </select>
        </label>
        <div>
          <span>Current leader</span>
          <strong>{leader?.club ?? "Not available"}</strong>
        </div>
        <div>
          <span>Exact-position probability</span>
          <strong>
            {leader ? formatProbability(leader.probability, 2) : "Not available"}
          </strong>
        </div>
        <button
          disabled={!leader}
          onClick={() => leader && setSelectedClub(leader.club)}
          type="button"
        >
          Inspect distribution
        </button>
      </div>

      <div className="standings-table-wrap">
        <table className="standings-table">
          <thead>
            <tr>
              <th scope="col">Expected</th>
              <th scope="col">Club</th>
              <th scope="col">Average rank</th>
              <th scope="col">Expected points</th>
              <th scope="col">Most likely</th>
              <th scope="col">Top 4</th>
              <th scope="col">{ordinal(focusPosition)}</th>
              <th scope="col">Relegation</th>
            </tr>
          </thead>
          <tbody>
            {standings.map((team, index) => (
              <tr
                className={selectedClub === team.club ? "selected" : ""}
                key={team.club}
                onClick={() => setSelectedClub(team.club)}
              >
                <td>
                  <span className="expected-rank">{index + 1}</span>
                </td>
                <th scope="row">
                  <button onClick={() => setSelectedClub(team.club)} type="button">
                    {team.club}
                  </button>
                </th>
                <td>{team.expected_position.toFixed(2)}</td>
                <td>{team.expected_points.toFixed(1)}</td>
                <td>{ordinal(team.most_likely_position)}</td>
                <td>{formatProbability(team.top_four_probability, 1)}</td>
                <td>
                  {formatProbability(
                    positionMap.get(`${team.club}:${focusPosition}`)
                      ?.probability ?? null,
                    1,
                  )}
                </td>
                <td
                  className={
                    team.relegation_probability >= 0.4 ? "risk-high" : ""
                  }
                >
                  {formatProbability(team.relegation_probability, 1)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="position-detail">
        <div className="position-detail-heading">
          <div>
            <p className="section-index">Position probability</p>
            <h3>{selectedClub}</h3>
          </div>
          <p>
            Every cell is the share of simulated seasons ending at that exact
            position. Dark cells are possible; brighter cells are more likely.
          </p>
        </div>
        <div className="distribution-bars" aria-label={`${selectedClub} position probabilities`}>
          {selectedDistribution.map((row) => (
            <div key={row.position}>
              <span>{ordinal(row.position)}</span>
              <i>
                <b style={{ width: `${row.probability * 100}%` }} />
              </i>
              <strong>{formatProbability(row.probability, 2)}</strong>
            </div>
          ))}
        </div>
      </div>

      <div className="heatmap-block">
        <div className="position-detail-heading">
          <div>
            <p className="section-index">All clubs × all positions</p>
            <h3>Position probability heatmap</h3>
          </div>
          <p>Scroll horizontally on smaller screens. Select any club row for detail.</p>
        </div>
        <div className="heatmap-scroll">
          <div
            className="position-heatmap"
            style={{
              gridTemplateColumns: `minmax(170px, 1fr) repeat(${data.meta.team_count}, 42px)`,
            }}
          >
            <span className="heatmap-corner">Club</span>
            {Array.from({ length: data.meta.team_count }, (_, index) => index + 1).map(
              (position) => (
                <strong
                  className={
                    position === focusPosition ? "focus-position" : ""
                  }
                  key={position}
                >
                  {position}
                </strong>
              ),
            )}
            {standings.map((team) => (
              <div className="heatmap-row" key={team.club}>
                <button
                  className={selectedClub === team.club ? "selected" : ""}
                  onClick={() => setSelectedClub(team.club)}
                  type="button"
                >
                  {team.club}
                </button>
                {Array.from(
                  { length: data.meta.team_count },
                  (_, index) => index + 1,
                ).map((position) => {
                  const row = positionMap.get(`${team.club}:${position}`);
                  const probability = row?.probability ?? 0;
                  return (
                    <span
                      className={
                        position === focusPosition ? "focus-position" : ""
                      }
                      key={position}
                      style={{
                        backgroundColor: `rgba(201, 246, 107, ${Math.min(
                          0.88,
                          probability * 2.4,
                        )})`,
                        color: probability > 0.32 ? "#0a0d0b" : undefined,
                      }}
                      title={`${team.club}, ${ordinal(position)}: ${formatProbability(
                        probability,
                        2,
                      )}`}
                    >
                      {probability >= 0.01
                        ? `${Math.round(probability * 100)}`
                        : "·"}
                    </span>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="table-backtest">
        <div>
          <p className="section-index">Table backtest · 2006–2025</p>
          <h3>Position distributions beat uniform baselines.</h3>
          <p>
            Each fold fits only on earlier seasons, simulates the target season,
            and scores the probability assigned to every club&apos;s actual rank.
          </p>
        </div>
        <article>
          <span>Position log loss</span>
          <strong>{positionLogLoss.toFixed(3)}</strong>
          <small>Uniform {uniformLogLoss.toFixed(3)}</small>
        </article>
        <article>
          <span>Expected-rank error</span>
          <strong>{positionMae.toFixed(2)}</strong>
          <small>Uniform {uniformMae.toFixed(2)} places</small>
        </article>
        <article>
          <span>Rank correlation</span>
          <strong>
            {metric(positionScores, "rank_correlation").toFixed(2)}
          </strong>
          <small>{data.position_backtest.fold_count} preseason folds</small>
        </article>
        <article
          className={data.position_backtest.acceptance.passed ? "passed" : "failed"}
        >
          <span>Table backtest</span>
          <strong>
            {data.position_backtest.acceptance.passed ? "Passed" : "Review"}
          </strong>
          <small>
            {data.position_backtest.simulations_per_fold.toLocaleString()} runs per fold
          </small>
        </article>
      </div>
    </section>
  );
}
