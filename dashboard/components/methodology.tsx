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
          <p className="section-index">05 / research notes</p>
          <h2>How to read the model</h2>
        </div>
        <p>
          The output is a calibrated distribution, not a claim that one future
          is certain. Expand the notes for assumptions and limitations.
        </p>
      </div>

      <div className="method-grid">
        <details open>
          <summary>What goes into a match?</summary>
          <p>
            Recency-weighted team strength, home advantage, score dependence,
            squad values, promotion shrinkage, and available de-vigged market
            probabilities become an expected score matrix and calibrated 1X2
            forecast.
          </p>
        </details>
        <details>
          <summary>What is simulated?</summary>
          <p>
            All {formatInteger(data.meta.fixture_count)} fixtures are sampled in
            each season. Points, goal difference, and goals scored determine the
            table. The same recorded seed makes the run reproducible.
          </p>
        </details>
        <details>
          <summary>What does convergence mean?</summary>
          <p>
            Early checkpoint movement is Monte Carlo noise. A line that changes
            very little from one to five million runs has a stable estimated
            title probability under this model.
          </p>
        </details>
        <details>
          <summary>Data coverage and limitations</summary>
          <p>
            {alignment
              ? `${alignment.matched_team_count} of ${alignment.official_team_count} official teams matched the live squad-value source.`
              : "Source alignment was not available for this run."}{" "}
            The live squad-value coefficient remains deliberately conservative,
            and exact TFF head-to-head mini-table tie-breaking is scheduled for
            a later engine refinement.
          </p>
        </details>
      </div>
    </section>
  );
}

