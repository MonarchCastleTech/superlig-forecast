import { formatInteger, type DashboardPayload } from "@/lib/dashboard-data";

type MethodologyProps = {
  data: DashboardPayload;
};

export function Methodology({ data }: MethodologyProps) {
  const alignment = data.meta.source_alignment;

  return (
    <section className="method-section" id="methodology">
      <div className="section-heading">
        <div>
          <p className="section-index">05 / methods</p>
          <h2>Methodology and interpretation</h2>
        </div>
        <p>
          A transparent summary of the estimand, information set, validation
          protocol, and known boundaries behind the published probabilities.
        </p>
      </div>

      <div className="method-grid">
        <article>
          <h3>Forecast target</h3>
          <p>
            The model estimates each remaining fixture&apos;s home-win, draw,
            and away-win probability and the distribution of final league
            positions. It does not publish exact-score predictions.
          </p>
        </article>
        <article>
          <h3>Data provenance</h3>
          <p>
            Point-in-time Turkish league results, fixtures, squad membership,
            player market values, and available pre-match odds are normalized
            into versioned snapshots. Source timestamps and identifiers are
            retained so every forecast can be audited and reproduced.
          </p>
        </article>
        <article>
          <h3>Temporal integrity</h3>
          <p>
            A forecast may use only information available before its prediction
            date. Historical evaluation uses expanding windows: each test
            season is scored after training exclusively on earlier seasons,
            preventing future results or future valuations from leaking back.
          </p>
        </article>
        <article>
          <h3>Structural model</h3>
          <p>
            A recency-weighted Dixon–Coles goal model estimates attacking and
            defensive strength, home advantage, and low-score dependence.
            Promoted clubs are partially pooled toward their prior-division
            evidence rather than treated as established top-flight teams.
          </p>
        </article>
        <article>
          <h3>Market-value adjustment</h3>
          <p>
            Current squad value supplies a deliberately conservative strength
            adjustment. The coefficient is selected inside historical folds,
            so a large squad cannot override observed match performance simply
            because its published valuation is high.
          </p>
        </article>
        <article>
          <h3>Current-season state</h3>
          <p>
            Completed official results are fixed in the starting table; only
            unplayed fixtures are sampled.{" "}
            {alignment
              ? `${alignment.matched_team_count} of ${alignment.official_team_count} official teams matched the current squad-value source in this publication.`
              : "The source-alignment audit was unavailable for this publication."}
          </p>
        </article>
        <article>
          <h3>Monte Carlo estimation</h3>
          <p>
            Each of {formatInteger(data.meta.simulations)} season paths samples
            every remaining fixture, then applies points, goal difference, and
            goals scored to form a possible table. A recorded random seed makes
            the published run exactly repeatable.
          </p>
        </article>
        <article>
          <h3>Backtest design</h3>
          <p>
            Twenty strict expanding-window folds compare the hybrid forecast
            with structural, market-only, and naive baselines using proper
            probability scores. A separate table backtest scores the
            probability assigned to clubs&apos; observed finishing positions.
          </p>
        </article>
        <article>
          <h3>Uncertainty</h3>
          <p>
            The convergence chart and 95% Monte Carlo intervals describe
            finite-simulation noise conditional on this model. They do not
            include every form of model, data, injury, transfer, or future-event
            uncertainty.
          </p>
        </article>
        <article>
          <h3>Limitations</h3>
          <p>
            Forecasts can be wrong and change after new matches or transfers.
            Squad valuations are imperfect proxies, rare events are difficult
            to calibrate, and exact TFF head-to-head mini-table tie-breaking is
            currently approximated by later table criteria.
          </p>
        </article>
      </div>
    </section>
  );
}
