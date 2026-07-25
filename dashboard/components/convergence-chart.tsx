"use client";

import { useMemo } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  formatInteger,
  formatProbability,
  type DashboardPayload,
} from "@/lib/dashboard-data";

const palette = [
  "#c9f66b",
  "#62d3c5",
  "#ff6b5f",
  "#5ba8ff",
  "#f7bf65",
  "#d18cff",
  "#f2efe5",
  "#84a98c",
];

function clubColor(club: string): string {
  let hash = 0;
  for (const character of club) hash = (hash * 31 + character.charCodeAt(0)) | 0;
  return palette[Math.abs(hash) % palette.length];
}

type ConvergenceChartProps = {
  data: DashboardPayload;
  selectedCheckpoint: number;
  selectedClub: string;
  visibleClubs: Set<string>;
  onSelectClub: (club: string) => void;
  onToggleClub: (club: string) => void;
};

export function ConvergenceChart({
  data,
  selectedCheckpoint,
  selectedClub,
  visibleClubs,
  onSelectClub,
  onToggleClub,
}: ConvergenceChartProps) {
  const chartData = useMemo(() => {
    return data.meta.checkpoints.map((checkpoint) => {
      const point: Record<string, number> = {
        simulation_count: checkpoint,
      };
      for (const row of data.convergence) {
        if (row.simulation_count === checkpoint) {
          point[row.club] = row.champion_probability;
        }
      }
      return point;
    });
  }, [data]);

  return (
    <article className="panel convergence-panel" aria-labelledby="convergence-heading">
      <div className="panel-heading">
        <div>
          <p className="section-index">Published audit trail</p>
          <h2 id="convergence-heading">Published reference convergence</h2>
        </div>
        <span>95% uncertainty tracked</span>
      </div>

      <div
        className="chart-shell"
        role="img"
        aria-label="Championship probabilities as simulation count increases"
      >
        <ResponsiveContainer width="100%" height={390}>
          <LineChart data={chartData} margin={{ top: 18, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid stroke="#2a2f2b" strokeDasharray="2 6" vertical={false} />
            <XAxis
              dataKey="simulation_count"
              stroke="#82877f"
              tickFormatter={(value: number) =>
                value >= 1_000_000 ? `${value / 1_000_000}m` : `${value / 1_000}k`
              }
            />
            <YAxis
              domain={[0, 0.65]}
              stroke="#82877f"
              tickFormatter={(value: number) => `${Math.round(value * 100)}%`}
            />
            <Tooltip
              contentStyle={{
                background: "#111512",
                border: "1px solid #414840",
                borderRadius: 0,
              }}
              formatter={(value) => formatProbability(Number(value), 2)}
              labelFormatter={(value) => `${formatInteger(Number(value))} simulations`}
            />
            <ReferenceLine
              x={selectedCheckpoint}
              stroke="#f3f0e8"
              strokeDasharray="3 4"
            />
            {[...visibleClubs].map((club) => (
              <Line
                activeDot={{ r: 5 }}
                animationDuration={360}
                dataKey={club}
                dot={{ r: 2 }}
                isAnimationActive
                key={club}
                name={club}
                stroke={clubColor(club)}
                strokeWidth={club === selectedClub ? 3.5 : 2}
                type="monotone"
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="club-toggles" aria-label="Visible clubs">
        {data.championship.map((team) => (
          <div className={selectedClub === team.club ? "focused" : ""} key={team.club}>
            <button
              aria-pressed={visibleClubs.has(team.club)}
              onClick={() => onToggleClub(team.club)}
              style={{ "--club-color": clubColor(team.club) } as React.CSSProperties}
              type="button"
            >
              <i />
              {team.club}
            </button>
            <button
              className="focus-club"
              onClick={() => onSelectClub(team.club)}
              type="button"
              aria-label={`Focus ${team.club}`}
            >
              {formatProbability(team.champion_probability, 1)}
            </button>
          </div>
        ))}
      </div>

      <details className="accessible-data">
        <summary>Read convergence data as text</summary>
        <ul>
          {data.championship.slice(0, 8).map((team) => (
            <li key={team.club}>
              {team.club}: {formatProbability(team.champion_probability, 2)}
            </li>
          ))}
        </ul>
      </details>
    </article>
  );
}
