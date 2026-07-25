from typer.testing import CliRunner
from pathlib import Path
import json

import pytest
import superlig_forecast.cli as cli_module
from superlig_forecast.cli import app
from superlig_forecast.data.transfermarkt_live import SquadFetchManifest


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


def test_fetch_current_squads_writes_complete_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    league_page = tmp_path / "league.html"
    league_page.write_text(
        '<a href="/club/kader/verein/36/saison_id/2026">Club</a>',
        encoding="utf-8",
    )

    def fake_fetch(links: object, output: Path) -> SquadFetchManifest:
        del links, output
        return SquadFetchManifest(
            fetched=("36",),
            unchanged=(),
            failed={},
            snapshot_timestamp="2026-07-25T12:00:00+00:00",
            source_urls={"36": "https://example.test/36"},
            complete=True,
        )

    monkeypatch.setattr(cli_module, "fetch_current_squad_pages", fake_fetch)
    manifest = tmp_path / "manifest.json"
    result = CliRunner().invoke(
        app,
        [
            "fetch-current-squads",
            "--league-page",
            str(league_page),
            "--output",
            str(tmp_path / "raw"),
            "--manifest",
            str(manifest),
        ],
    )
    assert result.exit_code == 0
    assert json.loads(manifest.read_text(encoding="utf-8"))["complete"] is True


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


def test_refresh_dashboard_promotes_valid_local_payload(tmp_path: Path) -> None:
    output = tmp_path / "dashboard.json"
    output.write_text('{"schema_version":1,"value":"stable"}', encoding="utf-8")
    result = CliRunner().invoke(
        app,
        [
            "refresh-dashboard",
            "--season",
            "2026",
            "--simulations",
            "1000",
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0
    assert "freshness" in json.loads(output.read_text(encoding="utf-8"))


def test_cli_exposes_complete_engine_command_surface() -> None:
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in {
        "fetch-data",
        "fetch-current-squads",
        "build-snapshots",
        "train-model",
        "backtest",
        "backtest-positions",
        "forecast-match",
        "forecast-season",
        "refresh-dashboard",
        "export-dashboard-data",
        "export-results",
    }:
        assert command in result.stdout
