"use client";

import { useMemo, useState } from "react";

import { BacktestPanel } from "@/components/backtest-panel";
import { ChampionshipRace } from "@/components/championship-race";
import { ConvergenceChart } from "@/components/convergence-chart";
import { FixtureExplorer } from "@/components/fixture-explorer";
import { Methodology } from "@/components/methodology";
import {
  formatInteger,
  rankAtCheckpoint,
  type DashboardPayload,
} from "@/lib/dashboard-data";

type DashboardAppProps = {
  data: DashboardPayload;
};

export function DashboardApp({ data }: DashboardAppProps) {
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
        <a className="brand" href="#top" aria-label="Forecast Lab home">
          <span className="brand-mark">SL</span>
          <span>
            Forecast Lab
            <small>Research build 01</small>
          </span>
        </a>
        <nav aria-label="Dashboard sections">
          <a href="#race">Race</a>
          <a href="#fixtures">Fixtures</a>
          <a href="#validation">Validation</a>
          <a href="#methodology">Method</a>
        </nav>
        <span className="model-status">
          <i />
          Model complete
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

      <section className="race-grid" id="race">
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

      <FixtureExplorer fixtures={data.fixtures} />
      <BacktestPanel backtest={data.backtest} />
      <Methodology data={data} />

      <footer>
        <div>
          <span className="brand-mark">SL</span>
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

