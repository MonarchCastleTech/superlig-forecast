import { useMemo, useState } from "react";

import { BacktestPanel } from "@/components/backtest-panel";
import { ChampionshipRace } from "@/components/championship-race";
import { ConvergenceChart } from "@/components/convergence-chart";
import { MatchOutlook } from "@/components/match-outlook";
import { Methodology } from "@/components/methodology";
import { StandingsPanel } from "@/components/standings-panel";
import { TitleProbabilityChart } from "@/components/title-probability-chart";
import {
  formatForecastUpdate,
  formatInteger,
  formatProbability,
  rankAtCheckpoint,
  type DashboardPayload,
} from "@/lib/dashboard-data";

type DashboardAppProps = {
  data: DashboardPayload;
};

export function DashboardApp({ data }: DashboardAppProps) {
  const mctLogo = `${import.meta.env.BASE_URL}brand/mct-icon.png`;
  const productLogo = `${import.meta.env.BASE_URL}brand/superlig-forecast-logo.png`;
  const finalCheckpoint = data.meta.checkpoints.at(-1) ?? data.meta.simulations;
  const [selectedClub, setSelectedClub] = useState(
    data.championship[0]?.club ?? "",
  );
  const [visibleClubs, setVisibleClubs] = useState<Set<string>>(
    () => new Set(data.championship.slice(0, 6).map((row) => row.club)),
  );
  const ranking = useMemo(
    () => rankAtCheckpoint(data, finalCheckpoint),
    [data, finalCheckpoint],
  );
  const leader = data.championship[0];
  const leaderStanding = data.expected_standings.find(
    (row) => row.club === leader?.club,
  );
  const completedFixtures = data.meta.completed_fixture_count ?? 0;

  function toggleClub(club: string) {
    setVisibleClubs((current) => {
      const next = new Set(current);
      if (next.has(club) && next.size > 1) {
        next.delete(club);
      } else {
        next.add(club);
      }
      return next;
    });
  }

  return (
    <main>
      <header className="masthead">
        <a
          className="brand"
          href="https://github.com/MonarchCastleTech"
          rel="noreferrer"
          target="_blank"
        >
          <img className="product-lockup" alt="Süper Lig Forecast" src={productLogo} />
          <span>
            MCT Forecast Lab
            <small>Forecasting Intelligence</small>
          </span>
        </a>
        <nav aria-label="Dashboard sections">
          <a href="#race">Title race</a>
          <a href="#standings">Table</a>
          <a href="#fixtures">Matches</a>
          <a href="#validation">Validation</a>
          <a href={`${import.meta.env.BASE_URL}methodology/`}>Methodology</a>
        </nav>
        <span className="model-status" data-testid="forecast-updated">
          <i />
          Updated {formatForecastUpdate(data.freshness.generated_at)}
        </span>
      </header>

      <aside className="forecast-notice" role="note">
        <strong>Research forecast</strong>
        <span>
          This is not betting advice and is not a guarantee of any match or
          season outcome.
        </span>
      </aside>

      <section
        aria-label="Data source freshness"
        className={`source-freshness source-${data.freshness.source_status}`}
        data-testid="source-freshness"
      >
        <strong>Source status · {data.freshness.source_status}</strong>
        <span>
          Matches {formatForecastUpdate(data.freshness.match_snapshot_at)}
          {" · "}Squad &amp; values{" "}
          {formatForecastUpdate(data.freshness.valuation_snapshot_at)}
        </span>
        <small>{data.freshness.source_notes.join(" ")}</small>
      </section>

      <section className="hero" id="top">
        <div>
          <p className="eyebrow">2026–27 Süper Lig · daily forecast brief</p>
          <h1>
            The season outlook,
            <br />
            <em>measured in probabilities.</em>
          </h1>
          <p className="hero-summary">
            Five million modelled season paths, recomputed from the latest
            accepted match and squad-value snapshots.
          </p>
        </div>
        <div className="hero-note">
          <p className="leader-kicker">Current title favourite</p>
          <strong className="leader-name">{leader?.club ?? "Pending"}</strong>
          <span className="leader-probability">
            {formatProbability(leader?.champion_probability ?? null)}
          </span>
          <dl>
            <div>
              <dt>Expected points</dt>
              <dd>{leaderStanding?.expected_points.toFixed(1) ?? "—"}</dd>
            </div>
            <div>
              <dt>Expected finish</dt>
              <dd>
                {leaderStanding
                  ? leaderStanding.expected_position.toFixed(1)
                  : "—"}
              </dd>
            </div>
            <div>
              <dt>Matches played</dt>
              <dd>{completedFixtures}</dd>
            </div>
            <div>
              <dt>Season paths</dt>
              <dd>{formatInteger(data.meta.simulations)}</dd>
            </div>
          </dl>
        </div>
      </section>

      <section id="race" className="reference-section">
        <div className="section-heading reference-heading">
          <div>
            <p className="section-index">01 · Title forecast</p>
            <h2>Where the championship probabilities stand today</h2>
          </div>
          <p>
            Published estimates from the latest validated five-million-path
            model run. Probability is uncertainty—not a promise.
          </p>
        </div>

        <TitleProbabilityChart data={data} />
        <section className="race-grid">
          <ChampionshipRace
            checkpoint={finalCheckpoint}
            ranking={ranking}
            selectedClub={selectedClub}
            onSelectClub={setSelectedClub}
          />
          <ConvergenceChart
            data={data}
            selectedCheckpoint={finalCheckpoint}
            selectedClub={selectedClub}
            visibleClubs={visibleClubs}
            onSelectClub={setSelectedClub}
            onToggleClub={toggleClub}
          />
        </section>
      </section>

      <StandingsPanel
        data={data}
        expectedStandings={data.expected_standings}
        positionRows={data.positions}
        sourceLabel="Latest published possible standings"
      />
      <MatchOutlook fixtures={data.fixtures} />
      <BacktestPanel backtest={data.backtest} />
      <Methodology data={data} />

      <footer>
        <div>
          <a
            href="https://github.com/MonarchCastleTech"
            rel="noreferrer"
            target="_blank"
          >
            <img alt="Monarch Castle Technologies" src={mctLogo} />
          </a>
          <strong>Süper Lig Forecast</strong>
        </div>
        <p>
          Independent sports analytics. Not betting advice and never a
          guarantee.
        </p>
        <p>
          Updated daily · Model {data.meta.model_version} · Seed {data.meta.seed}
        </p>
      </footer>
    </main>
  );
}
