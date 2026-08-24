import { useMemo, useState } from "react";

import {
  classifyMatchOutcome,
  formatProbability,
  type FixtureRow,
} from "@/lib/dashboard-data";

type MatchOutlookProps = {
  fixtures: FixtureRow[];
};

function outcomeMargin(fixture: FixtureRow): number {
  const values = [
    fixture.home_win_probability,
    fixture.draw_probability,
    fixture.away_win_probability,
  ].sort((left, right) => right - left);
  return values[0] - values[1];
}

function OutcomeBar({
  label,
  probability,
  tone,
}: {
  label: string;
  probability: number;
  tone: "home" | "draw" | "away";
}) {
  return (
    <div className={`outcome-row outcome-${tone}`}>
      <span>{label}</span>
      <div aria-hidden="true" className="outcome-track">
        <i style={{ width: `${probability * 100}%` }} />
      </div>
      <strong>{formatProbability(probability, 1)}</strong>
    </div>
  );
}

export function MatchOutlook({ fixtures }: MatchOutlookProps) {
  const [query, setQuery] = useState("");
  const visibleFixtures = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase("tr-TR");
    return [...fixtures]
      .filter(
        (fixture) =>
          !normalized ||
          fixture.home_team.toLocaleLowerCase("tr-TR").includes(normalized) ||
          fixture.away_team.toLocaleLowerCase("tr-TR").includes(normalized),
      )
      .sort((left, right) => outcomeMargin(right) - outcomeMargin(left));
  }, [fixtures, query]);

  return (
    <section className="match-outlook" id="fixtures" aria-labelledby="matches-heading">
      <div className="section-heading">
        <div>
          <p className="section-index">03 · Match outlook</p>
          <h2 id="matches-heading">Most likely match outcomes</h2>
        </div>
        <p>
          Home, draw, and away probabilities for remaining fixtures. These are
          outcome estimates, not guarantees.
        </p>
      </div>

      <label className="match-search">
        <span>Find a club</span>
        <input
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search remaining fixtures"
          type="search"
          value={query}
        />
      </label>

      <div className="match-grid">
        {visibleFixtures.map((fixture) => {
          const prediction = classifyMatchOutcome(fixture);
          return (
            <article
              className="match-card"
              key={`${fixture.home_team}-${fixture.away_team}`}
            >
              <header>
                <span>{fixture.home_team}</span>
                <b>vs</b>
                <span>{fixture.away_team}</span>
              </header>
              <div className="match-call">
                <p
                  className="prediction-status"
                  data-predicted={fixture.predicted === false ? "no" : "yes"}
                >
                  Predicted:{" "}
                  <strong>{fixture.predicted === false ? "No" : "Yes"}</strong>
                </p>
                <strong>{prediction.label}</strong>
                <small data-confidence={prediction.confidence}>
                  {prediction.confidence}
                </small>
              </div>
              <div className="outcome-bars">
                <OutcomeBar
                  label="Home"
                  probability={fixture.home_win_probability}
                  tone="home"
                />
                <OutcomeBar
                  label="Draw"
                  probability={fixture.draw_probability}
                  tone="draw"
                />
                <OutcomeBar
                  label="Away"
                  probability={fixture.away_win_probability}
                  tone="away"
                />
              </div>
            </article>
          );
        })}
      </div>

      {visibleFixtures.length === 0 ? (
        <p className="empty-state">No remaining fixture matches that club.</p>
      ) : null}
    </section>
  );
}
