import { useMemo } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatInteger, formatProbability } from "@/lib/dashboard-data";
import type { SimulationSnapshot } from "@/lib/live-simulation";

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

function ordinal(position: number): string {
  const remainder = position % 100;
  if (remainder >= 11 && remainder <= 13) return `${position}th`;
  if (position % 10 === 1) return `${position}st`;
  if (position % 10 === 2) return `${position}nd`;
  if (position % 10 === 3) return `${position}rd`;
  return `${position}th`;
}

function clubColor(club: string): string {
  let hash = 0;
  for (const character of club) {
    hash = (hash * 31 + character.charCodeAt(0)) | 0;
  }
  return palette[Math.abs(hash) % palette.length];
}

type LiveProbabilityChartProps = {
  history: SimulationSnapshot[];
  selectedPosition: number;
  visibleClubs: Set<string>;
};

export function LiveProbabilityChart({
  history,
  selectedPosition,
  visibleClubs,
}: LiveProbabilityChartProps) {
  const chartData = useMemo(
    () =>
      history
        .filter((snapshot) => snapshot.simulations > 0)
        .map((snapshot) => {
          const point: Record<string, number> = {
            simulations: snapshot.simulations,
          };
          for (const team of snapshot.teams) {
            point[team.club] =
              team.positionCounts[selectedPosition - 1] /
              snapshot.simulations;
          }
          return point;
        }),
    [history, selectedPosition],
  );
  const useLogScale =
    (chartData.at(-1)?.simulations ?? 0) >= 100 && chartData.length > 1;

  return (
    <div className="live-chart-block">
      <div className="panel-heading">
        <div>
          <p className="section-index">Live probability trace</p>
          <h3>Live probability · exact {ordinal(selectedPosition)} place</h3>
        </div>
        <span>{useLogScale ? "Log simulation axis" : "Warming up"}</span>
      </div>
      <div
        className="chart-shell"
        role="img"
        aria-label={`Live probabilities for exact ${ordinal(selectedPosition)} place`}
      >
        {chartData.length === 0 ? (
          <div className="chart-empty">
            Press play to watch the probability lines take shape.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={380}>
            <LineChart
              data={chartData}
              margin={{ top: 18, right: 12, left: -12, bottom: 0 }}
            >
              <CartesianGrid
                stroke="#2a2f2b"
                strokeDasharray="2 6"
                vertical={false}
              />
              <XAxis
                allowDataOverflow
                dataKey="simulations"
                domain={["dataMin", "dataMax"]}
                scale={useLogScale ? "log" : "linear"}
                stroke="#82877f"
                tickFormatter={(value: number) => formatInteger(value)}
                type="number"
              />
              <YAxis
                domain={[0, "auto"]}
                stroke="#82877f"
                tickFormatter={(value: number) =>
                  `${Math.round(value * 100)}%`
                }
              />
              <Tooltip
                contentStyle={{
                  background: "#111512",
                  border: "1px solid #414840",
                  borderRadius: 0,
                }}
                formatter={(value) => formatProbability(Number(value), 2)}
                labelFormatter={(value) =>
                  `${formatInteger(Number(value))} simulations`
                }
              />
              {[...visibleClubs].map((club) => (
                <Line
                  animationDuration={180}
                  dataKey={club}
                  dot={false}
                  isAnimationActive
                  key={club}
                  name={club}
                  stroke={clubColor(club)}
                  strokeWidth={2.4}
                  type="monotone"
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
