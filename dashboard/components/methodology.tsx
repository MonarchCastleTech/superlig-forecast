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
            TFF completed scores and Transfermarkt aggregate squad values feed
            the live forecast. Published JSON and player-state changes are
            versioned, but raw live pages are cached rather than permanently
            archived, so historical runs are not fully reproducible.
          </p>
        </article>
        <article>
          <h3>Temporal integrity</h3>
          <p>
            Historical evaluation uses expanding windows: each test season is
            scored after fitting the scoring-ratio model on earlier seasons.
            Current squad-value adjustments are not included in those folds.
          </p>
        </article>
        <article>
          <h3>Structural model</h3>
          <p>
            Recency-weighted home/away scoring and conceding ratios, shrunk
            toward league means, set expected goals. A fixed Dixon–Coles
            correction modifies four low-score cells; this is not a fitted
            log-linear Dixon–Coles model.
          </p>
        </article>
        <article>
          <h3>Market-value adjustment</h3>
          <p>
            Aggregate squad value supplies a fixed log-ratio strength
            adjustment with coefficient {data.meta.value_coefficient.toFixed(2)}.
            That coefficient is a modelling assumption and has not been selected
            or validated inside the checked-in historical folds.
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
            goals scored to form a possible table. The seed makes simulation
            repeatable only when code, dependencies, model artifact, and exact
            live input pages are also identical.
          </p>
        </article>
        <article>
          <h3>Backtest design</h3>
          <p>
            Twenty expanding-window folds assess the historical scoring-ratio
            core. Historical odds appear only in market and blended comparison
            baselines, not in the live title forecast. A separate table backtest
            also excludes the current squad-value adjustment.
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
            not implemented; unresolved ties use stable internal team order.
          </p>
        </article>
      </div>
    </section>
  );
}
