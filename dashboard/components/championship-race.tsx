import {
  formatCurrency,
  formatInteger,
  formatProbability,
  type ChampionshipRow,
} from "@/lib/dashboard-data";

type ChampionshipRaceProps = {
  checkpoint: number;
  ranking: ChampionshipRow[];
  selectedClub: string;
  onSelectClub: (club: string) => void;
};

export function ChampionshipRace({
  checkpoint,
  ranking,
  selectedClub,
  onSelectClub,
}: ChampionshipRaceProps) {
  const podium = ranking.slice(0, 3);

  return (
    <article className="panel race-panel" aria-labelledby="race-heading">
      <div className="panel-heading">
        <div>
          <p className="section-index">01 / championship</p>
          <h2 id="race-heading">Title forecast</h2>
        </div>
        <span>{formatInteger(checkpoint)} season paths</span>
      </div>

      <p className="panel-intro">
        Model probability of finishing first, estimated from the published
        Monte Carlo season paths.
      </p>

      <div className="title-podium" aria-label="Leading title probabilities">
        {podium.map((team, index) => (
          <button
            className={`podium-card podium-${index + 1} ${
              selectedClub === team.club ? "selected" : ""
            }`}
            key={team.club}
            onClick={() => onSelectClub(team.club)}
            type="button"
          >
            <span>#{index + 1}</span>
            <strong>{team.club}</strong>
            <b>{formatProbability(team.champion_probability, 1)}</b>
            <i
              style={{
                "--podium-fill": `${Math.max(team.champion_probability * 100, 1)}%`,
              } as React.CSSProperties}
            />
          </button>
        ))}
      </div>

      <div className="ranking-list">
        {ranking.map((team, index) => (
          <button
            aria-label={`${team.club}: ${formatProbability(
              team.champion_probability,
              2,
            )} title probability`}
            aria-pressed={selectedClub === team.club}
            className={`ranking-row ${selectedClub === team.club ? "selected" : ""}`}
            key={team.club}
            onClick={() => onSelectClub(team.club)}
            type="button"
          >
            <span className="rank-number">{String(index + 1).padStart(2, "0")}</span>
            <span className="club-block">
              <strong>{team.club}</strong>
              <small>{formatCurrency(team.squad_value_eur)} squad</small>
              <i
                style={{
                  width: `${Math.max(team.champion_probability * 100, 0.12)}%`,
                }}
              />
            </span>
            <span className="probability-block">
              <strong>{formatProbability(team.champion_probability, 2)}</strong>
              <small>
                ±{(team.ci95_half_width * 100).toFixed(3)} pp ·{" "}
                {formatInteger(team.champion_count)} titles
              </small>
            </span>
          </button>
        ))}
      </div>
    </article>
  );
}
