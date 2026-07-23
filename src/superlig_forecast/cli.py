"""Command-line interface."""

from pathlib import Path

import orjson
import typer

from superlig_forecast import __version__
from superlig_forecast.backtest.splits import walk_forward_folds
from superlig_forecast.data.warehouse import Warehouse
from superlig_forecast.data.tff import TFF_PAGES
from superlig_forecast.modeling.structural import score_matrix
from superlig_forecast.reporting.report import build_report
from superlig_forecast.simulation.rules import LeagueRules
from superlig_forecast.simulation.season import FixtureForecast, SeasonSimulator

app = typer.Typer(add_completion=False, no_args_is_help=True)


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
) -> None:
    """Inspect or fetch one configured source."""

    if source != "tff":
        raise typer.BadParameter(
            "only the tff source is available in this build", param_hint="source"
        )
    if not dry_run:
        raise typer.BadParameter(
            "live persistence is not available in this build", param_hint="dry-run"
        )
    del season
    for competition_id in TFF_PAGES:
        typer.echo(competition_id)


@app.command("build-snapshots")
def build_snapshots(output: Path = typer.Option(Path("data/model.duckdb"), "--output")) -> None:
    manifest = Warehouse(output).build([])
    typer.echo(manifest.model_dump_json())


@app.command("train-model")
def train_model(output: Path = typer.Option(Path("artifacts/model.json"), "--output")) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(orjson.dumps({"model": "hybrid", "status": "configured"}))
    typer.echo(str(output.resolve()))


@app.command("backtest")
def backtest(output: Path = typer.Option(Path("artifacts/backtest.json"), "--output")) -> None:
    seasons = [f"{year:04d}-{(year + 1) % 100:02d}" for year in range(2000, 2026)]
    folds = walk_forward_folds(seasons, "2005-06")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(orjson.dumps({"folds": len(folds), "first": folds[0].test_season}))
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
) -> None:
    if not demo:
        raise typer.BadParameter(
            "a normalized fixture dataset is required; use --demo for smoke runs"
        )
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
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "manifest.json"
    manifest_path.write_bytes(
        orjson.dumps(
            {
                "seed": seed,
                "n_simulations": simulations,
                "champion_counts": result.champion_counts,
                "model_version": __version__,
            },
            option=orjson.OPT_INDENT_2,
        )
    )
    typer.echo(str(manifest_path.resolve()))


@app.command("export-results")
def export_results(output: Path = typer.Option(Path("artifacts/report"), "--output")) -> None:
    path = build_report({"engine_version": __version__, "status": "generated"}, output)
    typer.echo(str(path.resolve()))
