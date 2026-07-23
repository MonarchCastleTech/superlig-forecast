from typer.testing import CliRunner
from pathlib import Path
import json

from superlig_forecast.cli import app


def test_version_option_reports_package_version() -> None:
    result = CliRunner().invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "superlig-forecast 0.1.0"


def test_tff_dry_run_lists_all_competition_families() -> None:
    result = CliRunner().invoke(
        app,
        ["fetch-data", "--source", "tff", "--season", "2026-27", "--dry-run"],
    )

    assert result.exit_code == 0
    assert result.stdout.splitlines() == ["TR1", "TR2", "TR3", "TR4", "TRC"]


def test_transfermarkt_dry_run_reports_pinned_kaggle_archive_url() -> None:
    result = CliRunner().invoke(
        app,
        ["fetch-data", "--source", "transfermarkt", "--season", "2026-27", "--dry-run"],
    )
    assert result.exit_code == 0
    assert result.stdout.strip() == (
        "https://www.kaggle.com/api/v1/datasets/download/"
        "davidcariboo/player-scores?datasetVersionNumber=673"
    )


def test_odds_dry_run_reports_pinned_kaggle_archive_url() -> None:
    result = CliRunner().invoke(
        app,
        ["fetch-data", "--source", "odds", "--season", "2026-27", "--dry-run"],
    )
    assert result.exit_code == 0
    assert result.stdout.strip() == (
        "https://www.kaggle.com/api/v1/datasets/download/"
        "ronaldoaf/football-matches-with-odds-from-oddsportal?datasetVersionNumber=4"
    )


def test_historical_results_dry_run_reports_pinned_archive_url() -> None:
    result = CliRunner().invoke(
        app,
        [
            "fetch-data",
            "--source",
            "historical-results",
            "--season",
            "2026-27",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    assert result.stdout.strip() == (
        "https://www.kaggle.com/api/v1/datasets/download/"
        "ycliffd/football-soccer-league-odds-and-results?datasetVersionNumber=4"
    )


def test_current_transfermarkt_dry_run_reports_season_page() -> None:
    result = CliRunner().invoke(
        app,
        [
            "fetch-data",
            "--source",
            "transfermarkt-current",
            "--season",
            "2026-27",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    assert result.stdout.strip().endswith("wettbewerb/TR1/plus/?saison_id=2026")


def test_demo_forecast_records_seed_and_simulation_count(tmp_path: Path) -> None:
    output = tmp_path / "forecast"
    result = CliRunner().invoke(
        app,
        [
            "forecast-season",
            "--demo",
            "--simulations",
            "1000",
            "--seed",
            "42",
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0
    manifest = json.loads(Path(result.stdout.strip()).read_text(encoding="utf-8"))
    assert manifest["seed"] == 42
    assert manifest["n_simulations"] == 1000
    assert (output / "position-probabilities.csv").exists()
    assert (output / "expected-standings.csv").exists()


def test_cli_exposes_complete_engine_command_surface() -> None:
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in {
        "fetch-data",
        "build-snapshots",
        "train-model",
        "backtest",
        "backtest-positions",
        "forecast-match",
        "forecast-season",
        "export-dashboard-data",
        "export-results",
    }:
        assert command in result.stdout
