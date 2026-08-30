import { useEffect, useState } from "react";
import { formatForecastUpdate, formatInteger, type DashboardPayload, validateDashboardPayload } from "@/lib/dashboard-data";

export function MethodologyLoader() {
  const [data, setData] = useState<DashboardPayload | null>(null);
  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/dashboard.json`)
      .then((response) => {
        if (!response.ok) throw new Error(`Data request failed: ${response.status}`);
        return response.json() as Promise<unknown>;
      })
      .then((payload) => setData(validateDashboardPayload(payload)));
  }, []);
  if (!data) return <main className="methodology-page"><p>Loading methodology…</p></main>;
  return <MethodologyPage data={data} />;
}

function Equation({ children }: { children: React.ReactNode }) {
  return <div className="equation">{children}</div>;
}

export function MethodologyPage({ data }: { data: DashboardPayload }) {
  const source = data.meta.source_alignment;
  return (
    <main className="methodology-page">
      <header className="methodology-masthead">
        <a href={import.meta.env.BASE_URL}>← Forecast</a>
        <span>MONARCH CASTLE TECHNOLOGIES · METHODOLOGY</span>
      </header>
      <section className="methodology-hero">
        <p className="eyebrow">Open methodology · model {data.meta.model_version}</p>
        <h1>How the Süper Lig forecast works</h1>
        <p>Official results, current squad strength and five million simulated seasons combine into one reproducible title forecast.</p>
        <dl>
          <div><dt>Season paths</dt><dd>{formatInteger(data.meta.simulations)}</dd></div>
          <div><dt>Deterministic seed</dt><dd>{data.meta.seed}</dd></div>
          <div><dt>Current release</dt><dd>{formatForecastUpdate(data.freshness.generated_at)}</dd></div>
          <div><dt>Clubs aligned</dt><dd>{source ? `${source.matched_team_count}/${source.official_team_count}` : "—"}</dd></div>
        </dl>
      </section>

      <article className="methodology-paper">
        <nav aria-label="Methodology contents">
          <a href="#pipeline">1. Pipeline</a><a href="#sources">2. Data</a><a href="#model">3. Model</a>
          <a href="#simulation">4. Simulation</a><a href="#validation">5. Validation</a><a href="#reproduce">6. Reproduce</a>
        </nav>

        <section id="pipeline">
          <span>01</span><div><h2>From matches to title probabilities</h2>
          <p>The live forecast and this methodology use the same published model output. Four stages produce every number on the title chart.</p>
          <ol className="runtime-chain" aria-label="Forecast calculation path">
            <li><strong>Lock the table:</strong> completed official matches fix points, goals scored and goals conceded.</li>
            <li><strong>Estimate each fixture:</strong> recent historical team strength sets the goal baseline; current aggregate squad value makes a conservative adjustment.</li>
            <li><strong>Simulate the run-in:</strong> every remaining fixture is sampled across {formatInteger(data.meta.simulations)} complete seasons.</li>
            <li><strong>Count outcomes:</strong> a club’s championship probability is its share of first-place finishes.</li>
          </ol></div>
        </section>

        <section id="sources">
          <span>02</span><div><h2>Data and autonomous refresh</h2>
          <p>TFF supplies official fixtures and completed scores. Current public Transfermarkt league and squad pages supply club-level squad totals. If GitHub cannot reach every squad page directly, automation validates all 18 aggregate totals from the league overview through a keyless public HTML reader, then tries a keyless CC0 structured player dataset; every route must still be current and complete.</p>
          <p>A GitHub Actions job runs every six hours over HTTPS. It requires all 18 clubs, reconciles match sources, runs the five-million-path forecast, applies freshness gates, and then runs Python, TypeScript, accessibility and static-build checks. A failed or stale refresh fails visibly and raises a repository alert; it cannot be reported as a successful update.</p>
          <p>Individual player names support transfer-change reporting. The title model itself uses only each club’s aggregate squad value—never personal profiles, social data or private information.</p></div>
        </section>

        <section id="model">
          <span>03</span><div><h2>Match probability model</h2>
          <p>The historical core uses five seasons of results with recency weight 0.68<sup>age</sup>. Separate home and away scoring and conceding rates are shrunk toward league averages with a six-match prior, reducing volatility for promoted and low-sample clubs.</p>
          <Equation>λ<sub>ij</sub> = clip(H · A<sup>home</sup><sub>i</sub> · D<sup>away</sup><sub>j</sub>, 0.2, 4.5)<br />ν<sub>ij</sub> = clip(A · A<sup>away</sup><sub>j</sub> · D<sup>home</sup><sub>i</sub>, 0.2, 4.5)</Equation>
          <p>Poisson score probabilities are corrected in the four lowest-score cells with the Dixon–Coles factor ρ = −0.05. Scores from 0 through 10 are retained and normalized.</p>
          <Equation>P(X=x,Y=y) ∝ τ<sub>ρ</sub>(x,y) · Pois(x;λ) · Pois(y;ν)</Equation>
          <p>Squad value adjusts the expected-goal balance symmetrically. The published coefficient is δ = {data.meta.value_coefficient.toFixed(2)}.</p>
          <Equation>r = (V<sub>home</sub> + €1m)/(V<sub>away</sub> + €1m)<br />λ′ = clip(λ · exp(0.5δ log r), 0.2, 4.5)<br />ν′ = clip(ν / exp(0.5δ log r), 0.2, 4.5)</Equation></div>
        </section>

        <section id="simulation">
          <span>04</span><div><h2>Season simulation</h2>
          <p>Every unplayed home-and-away fixture draws one score from its normalized matrix. Teams receive three points for a win and one for a draw, then rank by points, goal difference and goals scored. The deterministic seed {data.meta.seed} makes identical inputs produce identical output.</p>
          <Equation>P̂(team i wins) = N<sup>−1</sup> Σ<sub>s=1…N</sub> 𝟙(rank<sub>i,s</sub>=1)</Equation>
          <p>The displayed 95% Monte Carlo interval is 1.96√(P̂(1−P̂)/N). It measures simulation precision; real-world uncertainty remains broader because future injuries, tactics and transfers are unknowable.</p></div>
        </section>

        <section id="validation">
          <span>05</span><div><h2>Backtesting and calibration</h2>
          <p>Twenty expanding-window folds cover the 2006–2025 seasons. Each fold trains only on earlier seasons, then evaluates match probabilities with log loss and Brier score. A separate table backtest evaluates finishing-position distributions with 20,000 simulations per fold.</p>
          <Equation>Log loss = −n<sup>−1</sup>Σ log p<sub>i,yᵢ</sub><br />Brier = n<sup>−1</sup>Σ<sub>i</sub>Σ<sub>k</sub>(p<sub>ik</sub>−𝟙(yᵢ=k))²</Equation>
          <p>Historical odds appear only as comparison baselines. They never enter the live championship forecast. The validation artifacts test the scoring-ratio core and season simulator; the current squad-value coefficient remains an explicit modelling assumption.</p></div>
        </section>

        <section id="reproduce">
          <span>06</span><div><h2>Reproduce the computation</h2>
          <p>The code, locked dependencies, frozen model, simulation count and seed are public. The same inputs produce the same Monte Carlo result.</p>
          <pre><code>uv sync --locked{"\n"}uv run pytest -q{"\n"}uv run superlig forecast-season \{"\n"}  --season 2026 --simulations 5000000 --seed 202627 \{"\n"}  --model-artifact automation/seeds/model-2026-27.json \{"\n"}  --squad-page /path/to/squad-snapshot \{"\n"}  --tff-page /path/to/tff-snapshot \{"\n"}  --output artifacts/forecast</code></pre>
          <p>Git history preserves the model, publication payloads and detected squad changes. Exact third-party HTML pages are transient, so independently replaying an older publication also requires the source snapshots captured for that run.</p></div>
        </section>

        <section className="references">
          <span>07</span><div><h2>References</h2>
          <ol>
            <li>Dixon, M. J. &amp; Coles, S. G. (1997). <a href="https://doi.org/10.1111/1467-9876.00065">Modelling Association Football Scores and Inefficiencies in the Football Betting Market</a>.</li>
            <li>Brier, G. W. (1950). <a href="https://doi.org/10.1175/1520-0493(1950)078%3C0001:VOFEIT%3E2.0.CO;2">Verification of Forecasts Expressed in Terms of Probability</a>.</li>
            <li>Gneiting, T. &amp; Raftery, A. E. (2007). <a href="https://doi.org/10.1198/016214506000001437">Strictly Proper Scoring Rules, Prediction, and Estimation</a>.</li>
            <li><a href="https://github.com/MonarchCastleTech/superlig-forecast">Source code, tests and reproducibility assets</a>.</li>
          </ol></div>
        </section>
      </article>
    </main>
  );
}
