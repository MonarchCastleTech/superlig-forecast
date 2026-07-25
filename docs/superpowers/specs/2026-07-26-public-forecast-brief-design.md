# Public Süper Lig Forecast Brief Design

Date: 2026-07-26  
Status: Approved  
Owner: Monarch Castle Technologies

## Objective

Transform the existing simulator-facing dashboard into an English-language
public forecast brief. The public site presents one authoritative forecast
snapshot, refreshed daily from validated match, squad, transfer, and market
value inputs. It is an analytical research product, not a betting product or a
guarantee.

## Audience and product voice

The primary audience is a general football follower who wants to understand the
model's current view without operating a simulator. Secondary readers include
analysts who want to inspect validation evidence and reproduce the method.

Copy is concise, neutral, and probabilistic. Turkish club names remain in their
official form. Technical terms are defined at first use, and claims distinguish
model estimates from observed facts.

## Information architecture

1. **Masthead**
   - Official MCT mark and product name.
   - Season label.
   - Last successful update timestamp in Europe/Istanbul time.
   - Source freshness indicator.
2. **Forecast notice**
   - Permanent statement that the site is research and sports analytics.
   - Explicitly states that it is not betting advice and outcomes are not
     guaranteed.
3. **Forecast lead**
   - Current title favourite, title probability, expected points, and expected
     finishing position.
   - Summary of completed and remaining fixtures.
4. **Title race**
   - Ranked club probability display.
   - Five-million-run convergence chart.
   - Confidence intervals and hover detail.
5. **Possible final table**
   - Expected position and points.
   - Current points and goal difference.
   - Most likely position.
   - Title, top-four, and relegation probabilities.
   - Expandable probability distribution for every finishing position.
   - Clear zone cues without presenting any rank as certain.
6. **Match outlook**
   - Remaining fixtures only.
   - Home, draw, and away probabilities.
   - A labelled most-likely outcome: home winner, draw, or away winner.
   - No exact-score prediction.
   - Confidence language for close calls; a narrow plurality is not called a
     strong pick.
7. **Validation**
   - Plain-English headline findings from the strict 20-season backtest.
   - Match and table scoring metrics shown against their naïve or uniform
     baselines.
8. **Methodology**
   - Academic, reproducible specification with data provenance, temporal
     controls, equations, simulation process, evaluation, assumptions,
     limitations, and update policy.
9. **Footer**
   - MCT ownership.
   - Source repository and methodology links.
   - Daily update policy and disclaimer.

## Visual system

The visual language is sports intelligence rather than betting or gaming:

- Deep navy surfaces, MCT gold accents, white typography, and restrained
  probability gradients.
- Official MCT mark imported from the organization-controlled GitHub asset.
- Subtle grid and pitch-line texture; no casino or sportsbook motifs.
- Probability bars use length and labels, not color alone.
- Charts use animated entrance and hover transitions, accessible reduced-motion
  fallbacks, tooltips, focus states, and readable mobile layouts.
- Title probabilities use a ranked podium plus complete club bars.
- Convergence uses smooth lines, endpoint labels, and confidence context.
- Position distributions use a polished heatmap and expandable club detail.
- The match outlook uses outcome bars and confidence badges.

## Public behavior

The public interface has no editable simulation target, Play, Pause, Resume,
Stop, or Reset controls. It does not run user-triggered Monte Carlo simulations.
The only displayed results are the latest validated daily artifacts.

The dashboard may expose checkpoint history solely as model-convergence
evidence. It must not describe this as a live user simulation.

## Match outcome presentation

For each remaining fixture:

- `P(H)`, `P(D)`, and `P(A)` are displayed and sum to one within rounding.
- The largest probability determines the most-likely outcome.
- If draw is largest, the card says **Draw most likely**.
- If a club is largest, the card says **[Club] most likely winner**.
- The margin between the first and second probabilities determines confidence:
  under 5 percentage points is **Too close to call**, 5–12 points is
  **Slight edge**, and over 12 points is **Clear model edge**.
- Exact scores, betting odds, stakes, and return language are prohibited.

## Methodology contract

The methodology section documents:

1. **Forecast target** — final Süper Lig positions and remaining-match 1/X/2
   outcomes for 2026–27.
2. **Sources** — official TFF fixtures/results, current Transfermarkt squads and
   market values, optional football-data.org verification, and TheSportsDB free
   fallback.
3. **Temporal integrity** — each historical backtest fold trains only on data
   available before its target season; market observations are point-in-time.
4. **Structural model** — recency-weighted home/away attack and defence
   strengths with Poisson score generation and a Dixon–Coles low-score
   correction.
5. **Market-value adjustment** — conservative log-relative squad-value
   adjustment with a fixed coefficient disclosed as an assumption.
6. **Current-season state** — completed official results are fixed into points,
   goals for, and goals against; only remaining fixtures are simulated.
7. **Monte Carlo** — five million deterministic season paths using the published
   seed; ranking by points, goal difference, then goals scored.
8. **Evaluation** — strict 20-season expanding-window match and table backtests;
   log loss, Brier score, expected-rank error, and rank correlation compared
   with explicit baselines.
9. **Uncertainty** — probabilities are estimates conditional on the model and
   available inputs, not guarantees.
10. **Limitations** — exact TFF head-to-head mini-table tie-breaking is
    approximated after points; injuries, tactics, and unobserved shocks may not
    be fully represented; squad-value coefficient calibration remains a
    research item.

## Data and update flow

The scheduled GitHub Action runs daily:

1. Fetch current TFF pages for Süper Lig and lower divisions.
2. Fetch the current Transfermarkt league and squad pages.
3. Detect transfers and market-value changes against the prior state.
4. Reconcile official and free structured match feeds.
5. Fix completed results into the starting table.
6. Rebuild five million remaining-season paths from the compact trained model.
7. Export the public dashboard contract with source timestamps.
8. Run Python and dashboard quality gates.
9. Atomically commit validated data only.
10. Deploy the static site with GitHub Pages.

Failed, stale, or unreconciled inputs do not replace the last successful public
forecast.

## Repository and deployment

- Create public repository:
  `https://github.com/MonarchCastleTech/superlig-forecast`
- Publish GitHub Pages:
  `https://monarchcastletech.github.io/superlig-forecast/`
- Use `main` as the default branch.
- Retain scheduled update and Pages deployment workflows.
- Add the product to the governed MCT portfolio registry in
  `MonarchCastleTech/MonarchCastleTech.github.io`.
- The MCT product card links to the dashboard, repository, and methodology and
  identifies the update frequency as daily.

## README

The public README includes:

- Product purpose and live URL.
- Non-betting disclaimer.
- Current model and data-source summary.
- Daily update architecture.
- Local development commands.
- Complete verification commands.
- Backtest headline results with links to detailed artifacts.
- Reproducibility and limitations.
- MCT ownership and license information.

## Testing and acceptance

The release is accepted when:

- No simulation target or user-run simulation control is rendered.
- Last successful update time and source status are visible.
- The non-betting/non-guarantee warning is visible without interaction.
- Every match card displays valid 1/X/2 probabilities and a correct
  most-likely-outcome label.
- The standings remain usable on desktop and mobile.
- The methodology includes all ten contract topics.
- Existing payload validation, table probabilities, and backtest evidence remain
  intact.
- Dashboard unit tests, static build, typecheck, lint, production dependency
  audit, Python tests, coverage, mypy, and ruff pass.
- GitHub Pages serves the repository-subpath build.
- monarchcastle.tech includes a working product entry.

