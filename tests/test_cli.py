from typer.testing import CliRunner

from superlig_forecast.cli import app


def test_version_option_reports_package_version() -> None:
    result = CliRunner().invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "superlig-forecast 0.1.0"
