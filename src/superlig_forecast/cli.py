"""Command-line interface."""

from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import orjson
import polars as pl
import typer

from superlig_forecast import __version__
from superlig_forecast.backtest.walk_forward import (
    load_backtest_matches,
    run_walk_forward,
)
from superlig_forecast.data.fetch import FetchRequest, Fetcher
from superlig_forecast.data.historical_results import extract_historical_results_archive
from superlig_forecast.data.oddsportal_archive import extract_oddsportal_archive
from superlig_forecast.data.snapshots import SnapshotStore
from superlig_forecast.data.tff import TFF_PAGES, TffAdapter, decode_tff
from superlig_forecast.data.transfermarkt_live import (
    parse_current_players,
    parse_current_squad_links,
    parse_current_squad_values,
)
from superlig_forecast.data.transfermarkt_archive import extract_transfermarkt_archive
from superlig_forecast.data.warehouse import Warehouse
from superlig_forecast.forecasting.current_season import prepare_current_season
from superlig_forecast.modeling.structural import score_matrix
from superlig_forecast.modeling.team_strength import TeamStrengthModel, canonical_team_name
from superlig_forecast.reporting.charts import (
    backtest_log_loss_chart,
    championship_convergence,
)
from superlig_forecast.reporting.report import build_report
from superlig_forecast.simulation.rules import LeagueRules
from superlig_forecast.simulation.season import FixtureForecast, SeasonSimulator

app = typer.Typer(add_completion=False, no_args_is_help=True)
TRANSFERMARKT_DATABASE_URL = (
    "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/transfermarkt-datasets.duckdb"
)
TRANSFERMARKT_KAGGLE_URL = (
    "https://www.kaggle.com/api/v1/datasets/download/"
    "davidcariboo/player-scores?datasetVersionNumber=673"
)
ODDSPORTAL_KAGGLE_URL = (
    "https://www.kaggle.com/api/v1/datasets/download/"
    "ronaldoaf/football-matches-with-odds-from-oddsportal?datasetVersionNumber=4"
)
HISTORICAL_RESULTS_KAGGLE_URL = (
    "https://www.kaggle.com/api/v1/datasets/download/"
    "ycliffd/football-soccer-league-odds-and-results?datasetVersionNumber=4"
)
TRANSFERMARKT_CURRENT_URL = (
    "https://www.transfermarkt.com.tr/super-lig/startseite/wettbewerb/TR1/plus/?saison_id=2026"
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"superlig-forecast {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the package version and exit.",
    ),
) -> None:
    """Süper Lig forecasting engine."""


@app.command("fetch-data")
def fetch_data(
    source: str = typer.Option(..., "--source"),
    season: str = typer.Option(..., "--season"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    output: Path = typer.Option(Path("data/raw"), "--output"),
) -> None:
    """Inspect or fetch one configured source."""

    if source == "transfermarkt":
        if dry_run:
            typer.echo(TRANSFERMARKT_KAGGLE_URL)
            return
        result = Fetcher().fetch(
            FetchRequest(
                source="transfermarkt",
                url=TRANSFERMARKT_KAGGLE_URL,
                extension=".zip",
            )
        )
        typer.echo(str(SnapshotStore(output).put(result).payload_path.resolve()))
        return
    if source == "transfermarkt-current":
        if dry_run:
            typer.echo(TRANSFERMARKT_CURRENT_URL)
            return
        result = Fetcher().fetch(
            FetchRequest(
                source="transfermarkt-current",
                url=TRANSFERMARKT_CURRENT_URL,
                extension=".html",
            )
        )
        typer.echo(str(SnapshotStore(output).put(result).payload_path.resolve()))
        return
    if source == "odds":
        if dry_run:
            typer.echo(ODDSPORTAL_KAGGLE_URL)
            return
        result = Fetcher().fetch(
            FetchRequest(
                source="oddsportal",
                url=ODDSPORTAL_KAGGLE_URL,
                extension=".zip",
            )
        )
        typer.echo(str(SnapshotStore(output).put(result).payload_path.resolve()))
        return
    if source == "historical-results":
        if dry_run:
            typer.echo(HISTORICAL_RESULTS_KAGGLE_URL)
            return
        result = Fetcher().fetch(
            FetchRequest(
                source="historical-results",
                url=HISTORICAL_RESULTS_KAGGLE_URL,
                extension=".zip",
            )
        )
        typer.echo(str(SnapshotStore(output).put(result).payload_path.resolve()))
        return
    if source == "tff":
        if dry_run:
            for competition_id in TFF_PAGES:
                typer.echo(competition_id)
            return
        store = SnapshotStore(output)
        for competition_id, config in TFF_PAGES.items():
            endpoints = {
                f"tff-{competition_id}": config["page_id"],
                f"tff-{competition_id}-archive": config["archive_page_id"],
            }
            for source_name, page_id in endpoints.items():
                if source_name.endswith("-archive") and page_id == config["page_id"]:
                    continue
                url = f"https://www.tff.org/default.aspx?pageID={page_id}"
                result = Fetcher().fetch(
                    FetchRequest(source=source_name, url=url, extension=".html")
                )
                typer.echo(str(store.put(result).payload_path.resolve()))
        return
    raise typer.BadParameter(
        "source must be tff, transfermarkt, transfermarkt-current, odds, or historical-results",
        param_hint="source",
    )


@app.command("fetch-current-squads")
def fetch_current_squads(
    league_page: Path = typer.Option(..., "--league-page"),
    season: int = typer.Option(2026, "--season"),
    output: Path = typer.Option(Path("data/raw"), "--output"),
) -> None:
    """Snapshot every current top-flight club squad page."""

    links = parse_current_squad_links(league_page.read_text(encoding="utf-8"), season=season)
    store = SnapshotStore(output)
    fetcher = Fetcher()
    for club_id, url in sorted(links.items()):
        result = fetcher.fetch(
            FetchRequest(
                source=f"transfermarkt-squad-{club_id}",
                url=url,
                extension=".html",
            )
        )
        typer.echo(str(store.put(result).payload_path.resolve()))


@app.command("build-current-players")
def build_current_players(
    league_page: Path = typer.Option(..., "--league-page"),
    raw_dir: Path = typer.Option(Path("data/raw"), "--raw-dir"),
    warehouse_path: Path = typer.Option(Path("data/model.duckdb"), "--warehouse"),
    output: Path = typer.Option(Path("data/processed/current-players.parquet"), "--output"),
    season: int = typer.Option(2026, "--season"),
) -> None:
    """Normalize all snapshotted current squad pages into the warehouse."""

    league_html = league_page.read_text(encoding="utf-8")
    links = parse_current_squad_links(league_html, season=season)
    club_names = {item.club_id: item.club_name for item in parse_current_squad_values(league_html)}
    rows: list[dict[str, object]] = []
    for club_id in sorted(links):
        source_dir = raw_dir / f"transfermarkt-squad-{club_id}"
        snapshots = sorted(source_dir.glob("*.html"))
        if not snapshots:
            raise typer.BadParameter(
                f"no squad snapshot found for club {club_id}",
                param_hint="raw-dir",
            )
        players = parse_current_players(
            snapshots[-1].read_text(encoding="utf-8"),
            club_id=club_id,
            club_name=club_names[club_id],
        )
        for player in players:
            row = asdict(player)
            row["nationalities"] = ",".join(player.nationalities)
            row["season"] = season
            rows.append(row)
    output.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(rows).write_parquet(output)
    warehouse = Warehouse(warehouse_path)
    warehouse.build([])
    count = warehouse.load_current_players_parquet(output)
    typer.echo(
        orjson.dumps(
            {
                "players": count,
                "clubs": len(links),
                "parquet": str(output.resolve()),
                "warehouse": str(warehouse_path.resolve()),
            }
        ).decode()
    )


@app.command("build-snapshots")
def build_snapshots(
    output: Path = typer.Option(Path("data/model.duckdb"), "--output"),
    transfermarkt_archive: Path | None = typer.Option(None, "--transfermarkt-archive"),
    extract_dir: Path = typer.Option(Path("data/processed/transfermarkt"), "--extract-dir"),
    historical_results_archive: Path | None = typer.Option(None, "--historical-results-archive"),
    historical_extract_dir: Path = typer.Option(
        Path("data/processed/historical-results"), "--historical-extract-dir"
    ),
    odds_archive: Path | None = typer.Option(None, "--odds-archive"),
    odds_extract_dir: Path = typer.Option(Path("data/processed/oddsportal"), "--odds-extract-dir"),
) -> None:
    warehouse = Warehouse(output)
    manifest = warehouse.build([])
    counts: dict[str, int] = {}
    if transfermarkt_archive is not None:
        csv_paths = extract_transfermarkt_archive(transfermarkt_archive, extract_dir)
        counts = warehouse.load_transfermarkt_csvs(csv_paths)
    if historical_results_archive is not None:
        historical_csv = extract_historical_results_archive(
            historical_results_archive, historical_extract_dir
        )
        counts.update(warehouse.load_historical_results_csv(historical_csv))
    if odds_archive is not None:
        odds_csvs = extract_oddsportal_archive(odds_archive, odds_extract_dir)
        counts["oddsportal_matches"] = warehouse.load_oddsportal_csvs(odds_csvs)
    if transfermarkt_archive is not None and historical_results_archive is not None:
        counts["training_matches"] = warehouse.refresh_training_matches(
            use_oddsportal=odds_archive is not None
        )
    typer.echo(
        orjson.dumps(
            {
                "warehouse": str(output.resolve()),
                "data_hash": manifest.data_hash,
                "counts": counts,
            }
        ).decode()
    )


@app.command("train-model")
def train_model(
    output: Path = typer.Option(Path("artifacts/model.json"), "--output"),
    warehouse: Path = typer.Option(Path("data/model.duckdb"), "--warehouse"),
    before_season: int = typer.Option(2026, "--before-season"),
    squad_page: Path | None = typer.Option(None, "--squad-page"),
) -> None:
    matches = load_backtest_matches(warehouse)
    model = TeamStrengthModel.fit(
        [match.played() for match in matches],
        before_season=before_season,
    )
    payload: dict[str, object] = {
        "model": "recency-weighted-dixon-coles-market-value-hybrid",
        "model_version": __version__,
        "before_season": before_season,
        "historical_match_count": len(matches),
        "league_home_goals": model.league_home_goals,
        "league_away_goals": model.league_away_goals,
        "rho": model.rho,
        "team_rates": {team: asdict(rates) for team, rates in model.rates.items()},
    }
    if squad_page is not None:
        payload["current_squads"] = [
            asdict(item)
            for item in parse_current_squad_values(squad_page.read_text(encoding="utf-8"))
        ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2))
    typer.echo(str(output.resolve()))


@app.command("backtest")
def backtest(
    output: Path = typer.Option(Path("artifacts/backtest.json"), "--output"),
    warehouse: Path = typer.Option(Path("data/model.duckdb"), "--warehouse"),
    start_season: int = typer.Option(2006, "--start-season"),
    end_season: int = typer.Option(2025, "--end-season"),
    market_weight: float = typer.Option(0.9, "--market-weight", min=0.0, max=1.0),
) -> None:
    matches = load_backtest_matches(warehouse)
    report = run_walk_forward(
        matches,
        start_season=start_season,
        end_season=end_season,
        market_weight=market_weight,
    )
    scores = report.aggregate
    checks = {
        "exact_requested_fold_count": report.fold_count == end_season - start_season + 1,
        "hybrid_beats_naive_log_loss": scores.hybrid_log_loss < scores.naive_log_loss,
        "hybrid_beats_naive_brier": scores.hybrid_brier < scores.naive_brier,
        "hybrid_within_market_log_loss_tolerance": (
            scores.market_log_loss is None
            or scores.market_subset_hybrid_log_loss is None
            or scores.market_subset_hybrid_log_loss <= scores.market_log_loss + 0.01
        ),
    }
    payload = {
        "method": "strict-expanding-window",
        "start_season": start_season,
        "end_season": end_season,
        "market_weight": market_weight,
        "fold_count": report.fold_count,
        "match_count": report.match_count,
        "market_match_count": report.market_match_count,
        "aggregate": asdict(scores),
        "folds": [asdict(fold) for fold in report.folds],
        "acceptance": {"passed": all(checks.values()), "checks": checks},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    chart_path = output.with_name(f"{output.stem}-log-loss.png")
    chart_frame = pl.DataFrame(
        [
            {
                "season": fold.season,
                "naive_log_loss": fold.scores.naive_log_loss,
                "structural_log_loss": fold.scores.structural_log_loss,
                "hybrid_log_loss": fold.scores.hybrid_log_loss,
                "market_log_loss": fold.scores.market_log_loss,
            }
            for fold in report.folds
        ]
    )
    backtest_log_loss_chart(chart_frame, chart_path)
    payload["chart"] = str(chart_path.resolve())
    output.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2))
    typer.echo(str(output.resolve()))


@app.command("forecast-match")
def forecast_match(home_xg: float = 1.5, away_xg: float = 1.1) -> None:
    matrix = score_matrix(home_xg, away_xg, -0.05)
    typer.echo(
        orjson.dumps({"home_xg": home_xg, "away_xg": away_xg, "mass": matrix.sum()}).decode()
    )


@app.command("forecast-season")
def forecast_season(
    simulations: int = typer.Option(5_000_000, "--simulations", min=1),
    seed: int = typer.Option(202627, "--seed"),
    output: Path = typer.Option(Path("artifacts/forecast"), "--output"),
    demo: bool = typer.Option(False, "--demo"),
    warehouse: Path = typer.Option(Path("data/model.duckdb"), "--warehouse"),
    squad_page: Path | None = typer.Option(None, "--squad-page"),
    tff_page: Path | None = typer.Option(None, "--tff-page"),
    season: int = typer.Option(2026, "--season"),
    value_coefficient: float = typer.Option(0.1, "--value-coefficient", min=0.0, max=1.0),
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "manifest.json"
    if demo:
        teams = ("A", "B", "C", "D")
        matrix = score_matrix(1.5, 1.1, -0.05)
        fixtures = [
            FixtureForecast(home, away, matrix)
            for home in range(len(teams))
            for away in range(len(teams))
            if home != away
        ]
        result = SeasonSimulator(teams, LeagueRules.default()).simulate(
            fixtures, n=simulations, seed=seed
        )
        manifest_path.write_bytes(
            orjson.dumps(
                {
                    "seed": seed,
                    "n_simulations": simulations,
                    "champion_counts": result.champion_counts,
                    "model_version": __version__,
                    "demo": True,
                },
                option=orjson.OPT_INDENT_2,
            )
        )
        typer.echo(str(manifest_path.resolve()))
        return
    if squad_page is None:
        raise typer.BadParameter(
            "--squad-page is required for a real forecast",
            param_hint="squad-page",
        )
    historical = load_backtest_matches(warehouse)
    squads = parse_current_squad_values(squad_page.read_text(encoding="utf-8"))
    prepared = prepare_current_season(
        [match.played() for match in historical],
        squads,
        season=season,
        value_coefficient=value_coefficient,
    )
    checkpoints = tuple(
        sorted(
            {
                simulations,
                *(
                    value
                    for value in (10_000, 50_000, 100_000, 500_000, 1_000_000, 2_000_000)
                    if value <= simulations
                ),
            }
        )
    )
    checkpoint_results = SeasonSimulator(
        prepared.team_ids, LeagueRules.default()
    ).simulate_checkpoints(
        prepared.fixtures,
        checkpoints=checkpoints,
        seed=seed,
    )
    final = checkpoint_results[simulations]
    convergence_rows = [
        {
            "simulation_count": checkpoint,
            "club_id": club,
            "champion_probability": count / checkpoint,
        }
        for checkpoint, result in checkpoint_results.items()
        for club, count in result.champion_counts.items()
    ]
    convergence_frame = pl.DataFrame(convergence_rows)
    convergence_csv = output / "championship-convergence.csv"
    convergence_frame.write_csv(convergence_csv)
    convergence_chart = championship_convergence(
        convergence_frame, output / "championship-convergence.png"
    )
    probabilities = [
        {
            "club": club,
            "squad_value_eur": prepared.squad_values[club],
            "champion_count": count,
            "champion_probability": count / simulations,
            "ci95_half_width": SeasonSimulator.half_width(count, simulations),
        }
        for club, count in sorted(
            final.champion_counts.items(), key=lambda item: item[1], reverse=True
        )
    ]
    pl.DataFrame(probabilities).write_csv(output / "champion-probabilities.csv")
    pl.DataFrame([asdict(item) for item in prepared.expectations]).write_csv(
        output / "fixture-expectations.csv"
    )
    alignment: dict[str, object] | None = None
    if tff_page is not None:
        tff_matches = TffAdapter().parse_matches(
            decode_tff(tff_page.read_bytes()),
            observed_at=datetime.now(UTC),
            competition_id="TR1",
            season=f"{season}-{(season + 1) % 100:02d}",
        )
        official = {
            canonical_team_name(name)
            for match in tff_matches
            for name in (match.home_club_name, match.away_club_name)
        }
        market = {canonical_team_name(item.club_name) for item in squads}
        alignment = {
            "official_team_count": len(official),
            "market_team_count": len(market),
            "matched_team_count": len(official & market),
            "official_only": sorted(official - market),
            "market_only": sorted(market - official),
        }
    manifest_path.write_bytes(
        orjson.dumps(
            {
                "seed": seed,
                "n_simulations": simulations,
                "checkpoints": checkpoints,
                "season": f"{season}-{(season + 1) % 100:02d}",
                "team_count": len(prepared.team_ids),
                "fixture_count": len(prepared.fixtures),
                "value_coefficient": value_coefficient,
                "probabilities": probabilities,
                "team_source_alignment": alignment,
                "convergence_csv": str(convergence_csv.resolve()),
                "convergence_chart": str(convergence_chart.resolve()),
                "model_version": __version__,
                "demo": False,
            },
            option=orjson.OPT_INDENT_2,
        )
    )
    typer.echo(str(manifest_path.resolve()))


@app.command("export-results")
def export_results(output: Path = typer.Option(Path("artifacts/report"), "--output")) -> None:
    path = build_report({"engine_version": __version__, "status": "generated"}, output)
    typer.echo(str(path.resolve()))
