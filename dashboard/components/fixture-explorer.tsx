"use client";

import { useMemo, useState } from "react";

import {
  filterFixtures,
  formatProbability,
  type FixtureRow,
  type OutcomeFilter,
} from "@/lib/dashboard-data";

const PAGE_SIZE = 8;

function outcomeLabel(fixture: FixtureRow): string {
  const strongest = Math.max(
    fixture.home_win_probability,
    fixture.draw_probability,
    fixture.away_win_probability,
  );
  if (strongest === fixture.home_win_probability) return "Home lean";
  if (strongest === fixture.away_win_probability) return "Away lean";
  return "Draw lean";
}

type FixtureExplorerProps = {
  fixtures: FixtureRow[];
};

export function FixtureExplorer({ fixtures }: FixtureExplorerProps) {
  const [query, setQuery] = useState("");
  const [outcome, setOutcome] = useState<OutcomeFilter>("all");
  const [page, setPage] = useState(0);
  const [expanded, setExpanded] = useState<string | null>(null);
  const filtered = useMemo(
    () => filterFixtures(fixtures, query, outcome),
    [fixtures, query, outcome],
  );
  const maxPage = Math.max(0, Math.ceil(filtered.length / PAGE_SIZE) - 1);
  const visible = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  function updateQuery(value: string) {
    setQuery(value);
    setPage(0);
  }

  function updateOutcome(value: OutcomeFilter) {
    setOutcome(value);
    setPage(0);
  }

  return (
    <section className="fixture-section" id="fixtures">
      <div className="section-heading">
        <div>
          <p className="section-index">03 / match model</p>
          <h2>Fixture explorer</h2>
        </div>
        <p>
          Search all {fixtures.length} home-and-away fixtures. Open a match to
          inspect expected goals and the calibrated 1X2 distribution.
        </p>
      </div>

      <div className="fixture-toolbar">
        <label>
          <span>Find a club</span>
          <input
            onChange={(event) => updateQuery(event.target.value)}
            placeholder="Galatasaray, Amed, Beşiktaş…"
            type="search"
            value={query}
          />
        </label>
        <label>
          <span>Strongest outcome</span>
          <select
            onChange={(event) => updateOutcome(event.target.value as OutcomeFilter)}
            value={outcome}
          >
            <option value="all">Every match</option>
            <option value="home">Home win</option>
            <option value="draw">Draw</option>
            <option value="away">Away win</option>
          </select>
        </label>
        <div className="result-count">
          <strong>{filtered.length}</strong>
          <span>fixtures found</span>
        </div>
      </div>

      {visible.length === 0 ? (
        <div className="empty-state">
          <strong>No fixtures match those filters.</strong>
          <button
            onClick={() => {
              updateQuery("");
              updateOutcome("all");
            }}
            type="button"
          >
            Reset filters
          </button>
        </div>
      ) : (
        <div className="fixture-list">
          {visible.map((fixture) => {
            const key = `${fixture.home_team}-${fixture.away_team}`;
            const isExpanded = key === expanded;
            return (
              <article className={isExpanded ? "expanded" : ""} key={key}>
                <button
                  aria-expanded={isExpanded}
                  className="fixture-summary"
                  onClick={() => setExpanded(isExpanded ? null : key)}
                  type="button"
                >
                  <span className="fixture-clubs">
                    <strong>{fixture.home_team}</strong>
                    <i>vs</i>
                    <strong>{fixture.away_team}</strong>
                  </span>
                  <span className="xg-compact">
                    {fixture.home_expected_goals?.toFixed(2)} –{" "}
                    {fixture.away_expected_goals?.toFixed(2)} xG
                  </span>
                  <span className="outcome-lean">{outcomeLabel(fixture)}</span>
                  <span className="expand-mark">{isExpanded ? "−" : "+"}</span>
                </button>
                {isExpanded && (
                  <div className="fixture-detail">
                    {[
                      ["Home", fixture.home_win_probability],
                      ["Draw", fixture.draw_probability],
                      ["Away", fixture.away_win_probability],
                    ].map(([label, value]) => (
                      <div className="outcome-bar" key={String(label)}>
                        <span>{label}</span>
                        <i>
                          <b style={{ width: `${Number(value) * 100}%` }} />
                        </i>
                        <strong>{formatProbability(Number(value), 1)}</strong>
                      </div>
                    ))}
                    <p>
                      Expected score intensity: {fixture.home_expected_goals?.toFixed(2)}{" "}
                      home xG and {fixture.away_expected_goals?.toFixed(2)} away xG.
                    </p>
                  </div>
                )}
              </article>
            );
          })}
        </div>
      )}

      <div className="pagination">
        <button
          disabled={page === 0}
          onClick={() => setPage((current) => Math.max(0, current - 1))}
          type="button"
        >
          Previous
        </button>
        <span>
          Page {Math.min(page, maxPage) + 1} / {maxPage + 1}
        </span>
        <button
          disabled={page >= maxPage}
          onClick={() => setPage((current) => Math.min(maxPage, current + 1))}
          type="button"
        >
          Next
        </button>
      </div>
    </section>
  );
}

