"""Command-line interface."""

import typer

from superlig_forecast import __version__
from superlig_forecast.data.tff import TFF_PAGES

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
        raise typer.BadParameter("only the tff source is available in this build", param_hint="source")
    if not dry_run:
        raise typer.BadParameter("live persistence is not available in this build", param_hint="dry-run")
    del season
    for competition_id in TFF_PAGES:
        typer.echo(competition_id)
