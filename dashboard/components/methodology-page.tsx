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
  if (!data) return <main className="methodology-page"><p>Loading reproducibility record…</p></main>;
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
        <span>MONARCH CASTLE TECHNOLOGIES · METHODS</span>
      </header>
      <section className="methodology-hero">
        <p className="eyebrow">Research protocol · model {data.meta.model_version}</p>
        <h1>How the Süper Lig forecast is calculated</h1>
        <p>Estimand, source controls, equations, validation, uncertainty, and exact reproduction instructions for the published title probabilities.</p>
        <dl>
          <div><dt>Paths</dt><dd>{formatInteger(data.meta.simulations)}</dd></div>
          <div><dt>Seed</dt><dd>{data.meta.seed}</dd></div>
          <div><dt>Latest run</dt><dd>{formatForecastUpdate(data.freshness.generated_at)}</dd></div>
          <div><dt>Source match</dt><dd>{source ? `${source.matched_team_count}/${source.official_team_count}` : "Unavailable"}</dd></div>
        </dl>
      </section>

      <article className="methodology-paper">
        <nav aria-label="Methodology contents">
          <a href="#target">1. Target</a><a href="#sources">2. Sources</a><a href="#model">3. Model</a>
          <a href="#simulation">4. Simulation</a><a href="#validation">5. Validation</a><a href="#reproduce">6. Reproduce</a>
        </nav>

        <section id="target">
          <span>01</span><div><h2>Forecast target and information set</h2>
          <p>The target is each club’s probability of finishing first in the 2026–27 Süper Lig. A publication uses only snapshots observed by its generation time. Completed matches enter the starting table as facts; every unplayed home-and-away fixture is random.</p>
          <p>This is a conditional model probability, not a guarantee and not betting advice. It does not directly observe future injuries, tactics, discipline, or transfers after the source timestamp.</p></div>
        </section>

        <section id="sources">
          <span>02</span><div><h2>Sources and autonomous refresh</h2>
          <p>Official TFF pages are authoritative for clubs, fixtures, and results. The free TheSportsDB v1 endpoint (public key <code>123</code>) independently reconciles event records. Current Transfermarkt league and squad pages provide player membership and market-value snapshots. No paid API or manually maintained account is required.</p>
          <p>A six-hourly GitHub Actions job conditionally downloads pages, checks all 18 squads, compares player IDs with the previous state, reconciles match providers, blocks stale/conflicting candidates, runs all tests, and publishes only validated changes. Cached source files and timestamps form the audit trail.</p>
          <aside><strong>Failure rule.</strong> Partial squads, source conflicts, stale snapshots, or failed quality gates cannot replace the last validated public forecast.</aside></div>
        </section>

        <section id="model">
          <span>03</span><div><h2>Match model</h2>
          <p>A Dixon–Coles score model assigns Poisson intensities to home and away goals. Team attack and defence parameters, a league scoring level, and home advantage determine the baseline.</p>
          <Equation>λ<sub>ij</sub> = exp(μ + h + α<sub>i</sub> + β<sub>j</sub>)<br />ν<sub>ij</sub> = exp(μ + α<sub>j</sub> + β<sub>i</sub>)</Equation>
          <p>Here λ and ν are expected home and away goals; α is attack strength, β defence strength, μ the base log rate, and h home advantage. The Dixon–Coles factor τ<sub>ρ</sub>(x,y) adjusts 0–0, 0–1, 1–0 and 1–1 cells before the score matrix is normalized.</p>
          <Equation>P(X=x,Y=y) ∝ τ<sub>ρ</sub>(x,y) · Pois(x;λ) · Pois(y;ν)</Equation>
          <p>Current squad value changes expected-goal balance conservatively through the log value ratio. The published coefficient is {data.meta.value_coefficient.toFixed(2)} and is constrained by historical evaluation.</p>
          <Equation>λ′ = λ · exp(δ log(V<sub>home</sub>/V<sub>away</sub>)) &nbsp;;&nbsp; ν′ = ν · exp(−δ log(V<sub>home</sub>/V<sub>away</sub>))</Equation></div>
        </section>

        <section id="simulation">
          <span>04</span><div><h2>Season simulation and uncertainty</h2>
          <p>Each remaining fixture draws one score from its normalized matrix. The engine awards points, goal difference, and goals scored, ranks the resulting table, and repeats this process {formatInteger(data.meta.simulations)} times with NumPy’s deterministic random generator and seed {data.meta.seed}.</p>
          <Equation>P̂(team i wins) = N<sup>−1</sup> Σ<sub>s=1…N</sub> 𝟙(rank<sub>i,s</sub>=1)</Equation>
          <p>Reported Monte Carlo intervals use the binomial standard error: 1.96√(P̂(1−P̂)/N). They quantify simulation noise conditional on model and input data—not total real-world uncertainty.</p></div>
        </section>

        <section id="validation">
          <span>05</span><div><h2>Backtesting and calibration</h2>
          <p>Twenty expanding-window folds train only on seasons earlier than each test season. Match probabilities are compared with structural, market-only, and naive baselines. Proper scores reward honest probabilities.</p>
          <Equation>Log loss = −n<sup>−1</sup>Σ log p<sub>i,yᵢ</sub><br />Brier = n<sup>−1</sup>Σ<sub>i</sub>Σ<sub>k</sub>(p<sub>ik</sub>−𝟙(yᵢ=k))²</Equation>
          <p>Table forecasts are separately evaluated against observed finishing positions. Acceptance checks are machine-enforced before publication. Limitations include valuation measurement error, rare-event calibration, promoted-club uncertainty, and an approximation to exact TFF head-to-head mini-table tie-breaking.</p></div>
        </section>

        <section id="reproduce">
          <span>06</span><div><h2>Exact reproduction</h2>
          <p>Clone the repository and use the locked Python and Node dependencies. The workflow file is the executable protocol; its seed, simulation count, season, source paths, tests, and deployment are versioned together.</p>
          <pre><code>uv sync --locked{"\n"}uv run pytest -q{"\n"}uv run superlig forecast-season --season 2026 --simulations 5000000 --seed 202627 …{"\n"}cd dashboard &amp;&amp; npm ci &amp;&amp; npm test</code></pre>
          <p>Reproducing the same commit and cached snapshots yields the same simulated counts. A later live scrape is a new information set and should create a new dated publication rather than overwrite history.</p></div>
        </section>

        <section className="references">
          <span>07</span><div><h2>References and implementation</h2>
          <ol>
            <li>Dixon, M. J. &amp; Coles, S. G. (1997). <a href="https://doi.org/10.1111/1467-9876.00065">Modelling Association Football Scores and Inefficiencies in the Football Betting Market</a>.</li>
            <li>Brier, G. W. (1950). <a href="https://doi.org/10.1175/1520-0493(1950)078%3C0001:VOFEIT%3E2.0.CO;2">Verification of Forecasts Expressed in Terms of Probability</a>.</li>
            <li>Gneiting, T. &amp; Raftery, A. E. (2007). <a href="https://doi.org/10.1198/016214506000001437">Strictly Proper Scoring Rules, Prediction, and Estimation</a>.</li>
            <li><a href="https://github.com/MonarchCastleTech/superlig-forecast">Source code, data contracts, tests, and GitHub Actions protocol</a>.</li>
          </ol></div>
        </section>
      </article>
    </main>
  );
}
