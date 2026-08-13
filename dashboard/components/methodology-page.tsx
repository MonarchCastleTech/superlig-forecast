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
        <p>A code-matched description of the estimator, current inputs, simulation, validation evidence, and reproducibility limits behind the published title probabilities.</p>
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
          <p>The target is each club’s probability of finishing first in the 2026–27 Süper Lig, conditional on the model and accepted inputs. Completed TFF match scores enter the starting table as facts. The simulator treats every other ordered home-and-away pairing as unplayed.</p>
          <p>This is a conditional model probability, not a guarantee and not betting advice. It does not directly observe future injuries, tactics, discipline, or transfers after the source timestamp.</p></div>
        </section>

        <section id="sources">
          <span>02</span><div><h2>Sources and autonomous refresh</h2>
          <p>Official TFF pages supply the completed scores used by the live forecast. Current Transfermarkt league and squad pages supply club squad totals; individual player records are used to report detected squad changes, but the model consumes only each club’s aggregate market value. football-data.org, when a repository secret is configured, and otherwise the free TheSportsDB endpoint are reconciliation sources; their probabilities are not inputs to the live title forecast.</p>
          <p>A scheduled GitHub Actions job runs every six hours. It fetches TFF data, attempts a complete 18-club Transfermarkt refresh, rebuilds five million simulations from the frozen model artifact, applies freshness and reconciliation checks, runs the test/type/lint gates, and commits accepted JSON changes. If the Transfermarkt request fails, the runner attempts the dated squad snapshot embedded in the model artifact. A stale or conflicting candidate is rejected and the previously published forecast remains visible.</p>
          <aside><strong>Audit limit.</strong> Git history retains published dashboard JSON and detected player-state changes. Raw HTTP inputs are held in a bounded GitHub Actions cache, not an immutable public archive. Therefore a historical publication is not independently reproducible from the repository alone.</aside></div>
        </section>

        <section id="model">
          <span>03</span><div><h2>Production match estimator</h2>
          <p>The production estimator is not a maximum-likelihood log-linear Dixon–Coles fit. It uses recency-weighted home/away scoring and conceding ratios with a six-match empirical prior. The frozen 2026–27 artifact was trained from historical results before the season; fitting considers the preceding five seasons and assigns season weight 0.68<sup>age</sup>.</p>
          <Equation>λ<sub>ij</sub> = clip(H · A<sup>home</sup><sub>i</sub> · D<sup>away</sup><sub>j</sub>, 0.2, 4.5)<br />ν<sub>ij</sub> = clip(A · A<sup>away</sup><sub>j</sub> · D<sup>home</sup><sub>i</sub>, 0.2, 4.5)</Equation>
          <p>H and A are the recency-weighted league home- and away-goal means. Each A or D factor is a team’s correspondingly weighted scoring or conceding mean, shrunk toward the relevant league mean with six prior matches, then divided by that league mean. Home advantage is represented by separate H/A baselines and home/away team ratios—not a fitted h parameter.</p>
          <p>Independent Poisson probabilities are then adjusted in the 0–0, 0–1, 1–0 and 1–1 cells using the Dixon–Coles low-score factor. The production value of ρ is fixed at −0.05 rather than estimated. Scores from 0 through 10 are retained and the matrix is normalized.</p>
          <Equation>P(X=x,Y=y) ∝ τ<sub>ρ</sub>(x,y) · Pois(x;λ) · Pois(y;ν)</Equation>
          <p>Current squad value changes the goal balance through the smoothed value ratio below. The configured coefficient is δ = {data.meta.value_coefficient.toFixed(2)}. This coefficient is a modelling assumption; it has not been selected or validated by the checked-in historical folds.</p>
          <Equation>r = (V<sub>home</sub> + €1m)/(V<sub>away</sub> + €1m)<br />λ′ = clip(λ · exp(0.5δ log r), 0.2, 4.5)<br />ν′ = clip(ν / exp(0.5δ log r), 0.2, 4.5)</Equation></div>
        </section>

        <section id="simulation">
          <span>04</span><div><h2>Season simulation and uncertainty</h2>
          <p>Each remaining pairing draws one score from its normalized matrix. The engine awards points and ranks by points, goal difference, then goals scored. Exact TFF head-to-head mini-tables are not implemented; unresolved ties fall back to stable internal team order. This repeats {formatInteger(data.meta.simulations)} times with NumPy’s deterministic random generator and seed {data.meta.seed}.</p>
          <Equation>P̂(team i wins) = N<sup>−1</sup> Σ<sub>s=1…N</sub> 𝟙(rank<sub>i,s</sub>=1)</Equation>
          <p>Reported Monte Carlo intervals use the binomial standard error: 1.96√(P̂(1−P̂)/N). They quantify simulation noise conditional on model and input data—not total real-world uncertainty.</p></div>
        </section>

        <section id="validation">
          <span>05</span><div><h2>Backtesting and calibration</h2>
          <p>The checked-in match backtest contains 20 expanding-window folds for 2006–2025. Each fold trains the weighted-ratio estimator only on earlier seasons. It compares structural probabilities with a naive baseline and, where historical odds exist, de-vigged market probabilities plus a 90%-market blend. Betting odds are used only in this evaluation; they are not used by the production title forecast.</p>
          <Equation>Log loss = −n<sup>−1</sup>Σ log p<sub>i,yᵢ</sub><br />Brier = n<sup>−1</sup>Σ<sub>i</sub>Σ<sub>k</sub>(p<sub>ik</sub>−𝟙(yᵢ=k))²</Equation>
          <p>A separate 20-fold preseason table backtest runs 20,000 simulations per fold and scores finishing-position distributions. Neither checked-in backtest applies current squad-value adjustments, so the reported results validate the historical scoring-ratio core and simulation structure—not the complete live forecast or the δ = {data.meta.value_coefficient.toFixed(2)} choice. The artifacts are reused during scheduled publication rather than recomputed every six hours.</p>
          <aside><strong>Interpretation.</strong> These tests do not establish academic validation or full calibration of the published championship probabilities. Major unvalidated uncertainties include squad valuations, promoted teams, injuries, tactics, future transfers, and exact TFF tie-breaking.</aside></div>
        </section>

        <section id="reproduce">
          <span>06</span><div><h2>Rerunning the forecast and reproducibility limit</h2>
          <p>The Monte Carlo output is deterministic only when the code, locked dependencies, model artifact, exact TFF HTML, exact Transfermarkt league HTML, simulation count, and seed are identical. The repository includes the frozen model artifact but does not publicly preserve every raw live page used by every publication.</p>
          <pre><code>uv sync --locked{"\n"}uv run pytest -q{"\n"}uv run superlig forecast-season \{"\n"}  --season 2026 --simulations 5000000 --seed 202627 \{"\n"}  --model-artifact automation/seeds/model-2026-27.json \{"\n"}  --squad-page /path/to/exact-transfermarkt-league.html \{"\n"}  --tff-page /path/to/exact-tff-page.html \{"\n"}  --output artifacts/forecast{"\n"}cd dashboard &amp;&amp; npm ci &amp;&amp; npm test</code></pre>
          <p>This command describes the executable production path. Without the exact two live HTML inputs it produces a new information set, not an exact reproduction of an earlier publication. The six-hour workflow is the authoritative automation record.</p></div>
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
