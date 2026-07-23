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
  return (
    <article className="panel race-panel" aria-labelledby="race-heading">
      <div className="panel-heading">
        <div>
          <p className="section-index">01 / championship</p>
          <h2 id="race-heading">Championship race</h2>
        </div>
        <span>{formatInteger(checkpoint)} runs</span>
      </div>

      <div className="ranking-list">
        {ranking.map((team, index) => (
          <button
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

