import { formatProbability, type DashboardPayload } from "@/lib/dashboard-data";

const COLORS = ["#e61e2a", "#f2b705", "#111111", "#7a263a", "#f58220", "#2767c9"];

function clubKey(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/^istanbul\s+/, "")
    .replace(/\s+(a\.s\.|sk|jk|fk)$/i, "")
    .replace(/[^a-z0-9]/g, "");
}

function shortClub(value: string) {
  const names: Record<string, string> = {
    galatasaray: "Galatasaray",
    fenerbahce: "Fenerbahçe",
    besiktas: "Beşiktaş",
    basaksehir: "Başakşehir",
  };
  return names[clubKey(value)] ?? value;
}

function dateLabel(value: string) {
  return new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short" }).format(
    new Date(value),
  );
}

export function TitleProbabilityChart({ data }: { data: DashboardPayload }) {
  const fallback = [{
    generated_at: data.freshness.generated_at,
    probabilities: Object.fromEntries(
      data.championship.map((row) => [row.club, row.champion_probability]),
    ),
  }];
  const history = data.publication_history?.length ? data.publication_history : fallback;
  const leaders = data.championship.slice(0, 6);
  const points = leaders.map((club, index) => ({
    club,
    color: COLORS[index],
    values: history.map((snapshot) => {
      const match = Object.entries(snapshot.probabilities).find(
        ([name]) => clubKey(name) === clubKey(club.club),
      );
      return match?.[1] ?? 0;
    }),
  }));
  const width = 1120;
  const height = 490;
  const left = 62;
  const right = 155;
  const top = 34;
  const bottom = 62;
  const plotWidth = width - left - right;
  const plotHeight = height - top - bottom;
  const x = (index: number) => left + (history.length === 1 ? plotWidth : index * plotWidth / (history.length - 1));
  const y = (probability: number) => top + plotHeight * (1 - probability / 0.6);
  const labelYs: number[] = [];
  points.forEach((series, index) => {
    const raw = y(series.values.at(-1) ?? 0);
    labelYs[index] = index === 0 ? raw : Math.max(raw, labelYs[index - 1] + 25);
  });

  return (
    <article className="politico-chart" aria-labelledby="title-trend-heading">
      <div className="politico-chart-heading">
        <div>
          <p>Türkiye — 2026–27 Süper Lig</p>
          <h3 id="title-trend-heading">Chance of winning the championship</h3>
        </div>
        <span>MODEL HISTORY</span>
      </div>
      <p className="politico-deck">
        Each line is the probability published by a reproducible five-million-season simulation.
      </p>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Championship probability publication history">
        {[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6].map((tick) => (
          <g key={tick}>
            <line className="politico-gridline" x1={left} x2={left + plotWidth} y1={y(tick)} y2={y(tick)} />
            <text className="politico-axis-label" x={left - 10} y={y(tick) + 4} textAnchor="end">{Math.round(tick * 100)}%</text>
          </g>
        ))}
        {history.map((snapshot, index) => (
          <text className="politico-date-label" key={snapshot.generated_at} x={x(index)} y={height - 25} textAnchor={index === 0 ? "start" : index === history.length - 1 ? "end" : "middle"}>
            {dateLabel(snapshot.generated_at)}
          </text>
        ))}
        {points.map((series, seriesIndex) => {
          const path = series.values.map((value, index) => `${index ? "L" : "M"}${x(index)},${y(value)}`).join(" ");
          const endValue = series.values.at(-1) ?? 0;
          const endY = y(endValue);
          return (
            <g key={series.club.club}>
              <path className="politico-series" d={path} stroke={series.color} />
              {series.values.map((value, index) => <circle className="politico-point" cx={x(index)} cy={y(value)} fill={series.color} key={index} r="4" />)}
              <path className="politico-label-leader" d={`M${left + plotWidth + 4},${endY} L${left + plotWidth + 24},${labelYs[seriesIndex]}`} stroke={series.color} />
              <text className="politico-direct-label" fill={series.color} x={left + plotWidth + 30} y={labelYs[seriesIndex] + 5}>
                {shortClub(series.club.club)} {formatProbability(endValue, endValue < 0.01 ? 2 : 1)}
              </text>
            </g>
          );
        })}
      </svg>
      <small>Dates mark validated forecast publications. Lines grow automatically after every accepted refresh.</small>
    </article>
  );
}
