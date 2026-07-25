import { useMemo, useState } from "react";

import { BacktestPanel } from "@/components/backtest-panel";
import { ChampionshipRace } from "@/components/championship-race";
import { ConvergenceChart } from "@/components/convergence-chart";
import { FixtureExplorer } from "@/components/fixture-explorer";
import {
  deriveLiveTables,
  LiveSimulationPanel,
} from "@/components/live-simulation-panel";
import { Methodology } from "@/components/methodology";
import { StandingsPanel } from "@/components/standings-panel";
import { useLiveSimulation } from "@/hooks/use-live-simulation";
import {
  formatInteger,
  rankAtCheckpoint,
  type DashboardPayload,
} from "@/lib/dashboard-data";

type DashboardAppProps = {
  data: DashboardPayload;
};

export function DashboardApp({ data }: DashboardAppProps) {
  const mctLogo = `${import.meta.env.BASE_URL}brand/mct-icon.png`;
  const liveSimulation = useLiveSimulation(data);
  const finalCheckpoint = data.meta.checkpoints.at(-1) ?? data.meta.simulations;
  const [checkpoint, setCheckpoint] = useState(finalCheckpoint);
  const [selectedClub, setSelectedClub] = useState(
    data.championship[0]?.club ?? "",
  );
  const [visibleClubs, setVisibleClubs] = useState<Set<string>>(
    () => new Set(data.championship.slice(0, 6).map((row) => row.club)),
  );
  const ranking = useMemo(
    () => rankAtCheckpoint(data, checkpoint),
    [data, checkpoint],
  );
  const liveTables = useMemo(
    () =>
      liveSimulation.snapshot
        ? deriveLiveTables(liveSimulation.snapshot)
        : null,
    [liveSimulation.snapshot],
  );

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
          <img alt="Monarch Castle Technologies" src={mctLogo} />
          <span>
            MCT Forecast Lab
            <small>Forecasting Intelligence</small>
          </span>
        </a>
        <nav aria-label="Dashboard sections">
          <a href="#race">Race</a>
          <a href="#standings">Table</a>
          <a href="#fixtures">Fixtures</a>
          <a href="#validation">Validation</a>
          <a href="#methodology">Method</a>
        </nav>
        <span className="model-status">
          <i />
          Simulator {liveSimulation.status}
        </span>
      </header>

      <section className="hero" id="top">
        <div>
          <p className="eyebrow">2026–27 Süper Lig · preseason forecast</p>
          <h1>
            The title race,
            <br />
            <em>played five million times.</em>
          </h1>
        </div>
        <div className="hero-note">
          <p>
            A market-informed structural model trained on historical matches,
            players, lineups, squad values, and de-vigged match odds.
          </p>
          <dl>
            <div>
              <dt>Simulations</dt>
              <dd>{formatInteger(data.meta.simulations)}</dd>
            </div>
            <div>
              <dt>Backtest</dt>
              <dd>{data.backtest.fold_count} seasons</dd>
            </div>
            <div>
              <dt>Seed</dt>
              <dd>{data.meta.seed}</dd>
            </div>
          </dl>
        </div>
      </section>

      <div id="race">
        <LiveSimulationPanel data={data} controller={liveSimulation} />
      </div>

      <div className="reference-section">
        <div className="section-heading reference-heading">
          <div>
            <p className="section-index">Published reference</p>
            <h2>Precomputed five-million-run audit</h2>
          </div>
          <p>
            These frozen checkpoints remain available for reproducibility. The
            live player above is the primary simulation.
          </p>
        </div>
      <section className="checkpoint-strip" aria-label="Simulation checkpoint">
        <div>
          <span>Simulation checkpoint</span>
          <strong>{formatInteger(checkpoint)} seasons</strong>
        </div>
        <div className="checkpoint-buttons">
          {data.meta.checkpoints.map((value) => (
            <button
              className={value === checkpoint ? "active" : ""}
              key={value}
              onClick={() => setCheckpoint(value)}
              type="button"
            >
              {value >= 1_000_000
                ? `${value / 1_000_000}m`
                : `${value / 1_000}k`}
            </button>
          ))}
        </div>
        <p>
          Move through the run to see when the championship signal stabilizes.
        </p>
      </section>

      <section className="race-grid">
        <ChampionshipRace
          checkpoint={checkpoint}
          ranking={ranking}
          selectedClub={selectedClub}
          onSelectClub={setSelectedClub}
        />
        <ConvergenceChart
          data={data}
          selectedCheckpoint={checkpoint}
          selectedClub={selectedClub}
          visibleClubs={visibleClubs}
          onSelectClub={setSelectedClub}
          onToggleClub={toggleClub}
        />
      </section>
      </div>

      <StandingsPanel
        data={data}
        expectedStandings={liveTables?.expectedStandings}
        positionRows={liveTables?.positionRows}
        sourceLabel={
          liveTables
            ? "Live possible standings"
            : "Reference possible standings"
        }
      />
      <FixtureExplorer fixtures={data.fixtures} />
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
          <strong>Süper Lig Forecast Lab</strong>
        </div>
        <p>
          Forecast quality only. This research model is not betting advice.
        </p>
        <p>
          Model {data.meta.model_version} · Seed {data.meta.seed}
        </p>
      </footer>
    </main>
  );
}
