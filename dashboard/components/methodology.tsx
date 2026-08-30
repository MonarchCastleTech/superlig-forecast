import { formatInteger, type DashboardPayload } from "@/lib/dashboard-data";

type MethodologyProps = {
  data: DashboardPayload;
};

export function Methodology({ data }: MethodologyProps) {
  return (
    <section className="method-section" id="methodology">
      <div className="section-heading">
        <div>
          <p className="section-index">05 / methods</p>
          <h2>How the forecast is built</h2>
        </div>
        <p>
          Official results, current squad strength, a tested goal model and
          five million simulated seasons.
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
          <h3>Official inputs</h3>
          <p>
            TFF completed scores and Transfermarkt aggregate squad values feed
            the live forecast. Every accepted update must cover all 18 clubs
            and pass source reconciliation and freshness checks.
          </p>
        </article>
        <article>
          <h3>Historical testing</h3>
          <p>
            Twenty expanding-window folds test the scoring model on seasons it
            had not seen. Log loss and Brier score measure probability quality.
          </p>
        </article>
        <article>
          <h3>Goal model</h3>
          <p>
            Recency-weighted home/away scoring and conceding ratios, shrunk
            toward league means, set expected goals. A fixed Dixon–Coles
            correction improves the four lowest-score outcomes.
          </p>
        </article>
        <article>
          <h3>Squad strength</h3>
          <p>
            Aggregate squad value supplies a fixed log-ratio strength
            adjustment with coefficient {data.meta.value_coefficient.toFixed(2)},
            keeping the effect deliberately conservative.
          </p>
        </article>
        <article>
          <h3>Five million seasons</h3>
          <p>
            Completed results remain fixed. Each of {formatInteger(data.meta.simulations)}
            paths samples every unplayed fixture, then ranks the final table by
            points, goal difference and goals scored.
          </p>
        </article>
      </div>
    </section>
  );
}
