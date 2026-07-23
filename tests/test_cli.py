from typer.testing import CliRunner

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
