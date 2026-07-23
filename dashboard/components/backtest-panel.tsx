"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatInteger, type DashboardPayload } from "@/lib/dashboard-data";

type BacktestPanelProps = {
  backtest: DashboardPayload["backtest"];
};

function metric(
  values: Record<string, number | null>,
  key: string,
): number {
  return values[key] ?? Number.NaN;
}

export function BacktestPanel({ backtest }: BacktestPanelProps) {
  const naiveLogLoss = metric(backtest.aggregate, "naive_log_loss");
  const hybridLogLoss = metric(backtest.aggregate, "hybrid_log_loss");
  const naiveBrier = metric(backtest.aggregate, "naive_brier");
  const hybridBrier = metric(backtest.aggregate, "hybrid_brier");
  const chartData = backtest.folds.map((fold) => ({
    season: fold.season,
    naive: fold.scores.naive_log_loss,
    hybrid: fold.scores.hybrid_log_loss,
    structural: fold.scores.structural_log_loss,
  }));

  return (
    <section className="validation-section" id="validation">
      <div className="section-heading">
        <div>
          <p className="section-index">04 / evidence</p>
          <h2>Twenty-season validation</h2>
        </div>
        <p>
          Every scored season is a true expanding-window fold: only earlier
          matches are available when the next season is predicted.
        </p>
      </div>

      <div className="validation-grid">
        <div className="metric-stack">
          <article>
            <span>Hybrid log loss</span>
            <strong>{hybridLogLoss.toFixed(3)}</strong>
            <small>
              {(((naiveLogLoss - hybridLogLoss) / naiveLogLoss) * 100).toFixed(1)}%
              better than naive
            </small>
          </article>
          <article>
            <span>Hybrid Brier score</span>
            <strong>{hybridBrier.toFixed(3)}</strong>
            <small>
              {(((naiveBrier - hybridBrier) / naiveBrier) * 100).toFixed(1)}%
              lower error
            </small>
          </article>
          <article>
            <span>Scored matches</span>
            <strong>{formatInteger(backtest.match_count)}</strong>
            <small>{formatInteger(backtest.market_match_count)} with market data</small>
          </article>
          <article className={backtest.acceptance.passed ? "passed" : "failed"}>
            <span>Acceptance gate</span>
            <strong>{backtest.acceptance.passed ? "Passed" : "Review"}</strong>
            <small>{Object.keys(backtest.acceptance.checks).length} model checks</small>
          </article>
        </div>

        <article className="panel fold-chart">
          <div className="panel-heading">
            <div>
              <p className="section-index">2006 → 2025</p>
              <h3>Log loss by fold</h3>
            </div>
            <span>Lower is better</span>
          </div>
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={chartData} margin={{ top: 20, right: 12, left: -20 }}>
              <CartesianGrid stroke="#2a2f2b" strokeDasharray="2 6" vertical={false} />
              <XAxis dataKey="season" stroke="#82877f" />
              <YAxis domain={["dataMin - 0.05", "dataMax + 0.05"]} stroke="#82877f" />
              <Tooltip
                contentStyle={{
                  background: "#111512",
                  border: "1px solid #414840",
                  borderRadius: 0,
                }}
                formatter={(value) => Number(value).toFixed(3)}
              />
              <Legend />
              <Line
                dataKey="naive"
                dot={false}
                name="Naive"
                stroke="#6d736c"
                strokeWidth={1.5}
                type="monotone"
              />
              <Line
                dataKey="structural"
                dot={false}
                name="Structural"
                stroke="#62d3c5"
                strokeWidth={2}
                type="monotone"
              />
              <Line
                dataKey="hybrid"
                dot={false}
                name="Hybrid"
                stroke="#c9f66b"
                strokeWidth={3}
                type="monotone"
              />
            </LineChart>
          </ResponsiveContainer>
        </article>
      </div>
    </section>
  );
}

