from typer.testing import CliRunner
from pathlib import Path
import json
from types import SimpleNamespace

import pytest
import superlig_forecast.cli as cli_module
from superlig_forecast.cli import app
from superlig_forecast.data.structured_sources import ProviderBatch
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


def test_tff_fetch_accepts_an_explicit_official_base_url(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[object] = []

    class FakeFetcher:
        def fetch(self, request: object) -> object:
            requests.append(request)
            return request

    class FakeStore:
        def __init__(self, output: Path) -> None:
            del output

        def put(self, result: object) -> object:
            del result
            return SimpleNamespace(payload_path=tmp_path / "snapshot.html")

    monkeypatch.setattr(cli_module, "Fetcher", FakeFetcher)
    monkeypatch.setattr(cli_module, "SnapshotStore", FakeStore)

    result = CliRunner().invoke(
        app,
        [
            "fetch-data",
            "--source",
            "tff",
            "--season",
            "2026-27",
            "--tff-base-url",
            "http://www.tff.org",
            "--output",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert requests
    assert all(
        str(getattr(request, "url")).startswith(
            "http://www.tff.org/default.aspx?pageID=",
        )
        for request in requests
    )


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
    assert result.stdout.strip() == (
        "https://www.transfermarkt.com/super-lig/startseite/wettbewerb/TR1/plus/?saison_id=2026"
    )


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


def test_real_forecast_can_run_from_compact_model_artifact(tmp_path: Path) -> None:
    squad_page = tmp_path / "league.html"
    squad_page.write_text(
        """
        <table class="items">
        <thead><tr><th>marktwert_gesamt_anzeige</th></tr></thead><tbody>
          <tr class="odd">
            <td><a href="/a/startseite/verein/1/saison_id/2026">crest</a></td>
            <td class="hauptlink"><a title="A SK">A SK</a></td>
            <td class="zentriert">25</td><td>25</td><td>5</td><td>€1m</td>
            <td class="rechts"><a href="/a/kader/verein/1/saison_id/2026">€100m</a></td>
          </tr>
          <tr class="even">
            <td><a href="/b/startseite/verein/2/saison_id/2026">crest</a></td>
            <td class="hauptlink"><a title="B SK">B SK</a></td>
            <td class="zentriert">25</td><td>25</td><td>5</td><td>€1m</td>
            <td class="rechts"><a href="/b/kader/verein/2/saison_id/2026">€50m</a></td>
          </tr>
        </tbody></table>
        """,
        encoding="utf-8",
    )
    model_artifact = tmp_path / "model.json"
    model_artifact.write_text(
        json.dumps(
            {
                "league_home_goals": 1.5,
                "league_away_goals": 1.2,
                "rho": -0.05,
                "team_rates": {},
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "forecast"

    result = CliRunner().invoke(
        app,
        [
            "forecast-season",
            "--simulations",
            "100",
            "--model-artifact",
            str(model_artifact),
            "--squad-page",
            str(squad_page),
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["team_count"] == 2
    assert manifest["fixture_count"] == 2


def test_real_forecast_accepts_dated_json_squad_snapshot(tmp_path: Path) -> None:
    model_artifact = tmp_path / "model.json"
    model_artifact.write_text(
        json.dumps(
            {
                "league_home_goals": 1.5,
                "league_away_goals": 1.2,
                "rho": -0.05,
                "team_rates": {},
                "current_squads": [
                    {
                        "club_id": 1,
                        "club_name": "A SK",
                        "squad_size": 25,
                        "squad_value_eur": 100_000_000,
                    },
                    {
                        "club_id": 2,
                        "club_name": "B SK",
                        "squad_size": 25,
                        "squad_value_eur": 50_000_000,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "forecast"

    result = CliRunner().invoke(
        app,
        [
            "forecast-season",
            "--simulations",
            "100",
            "--model-artifact",
            str(model_artifact),
            "--squad-page",
            str(model_artifact),
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["team_count"] == 2
    assert manifest["fixture_count"] == 2


def test_update_current_changes_writes_player_state_and_change_feed(tmp_path: Path) -> None:
    league_page = tmp_path / "league.html"
    league_page.write_text(
        """
        <table class="items">
        <thead><tr><th>marktwert_gesamt_anzeige</th></tr></thead><tbody>
          <tr class="odd">
            <td><a href="/a/startseite/verein/1/saison_id/2026">crest</a></td>
            <td class="hauptlink"><a title="A SK">A SK</a></td>
            <td class="zentriert">1</td><td>25</td><td>1</td><td>€1m</td>
            <td class="rechts"><a href="/a/kader/verein/1/saison_id/2026">€4m</a></td>
          </tr>
        </tbody></table>
        """,
        encoding="utf-8",
    )
    squad_dir = tmp_path / "raw" / "transfermarkt-squad-1"
    squad_dir.mkdir(parents=True)
    (squad_dir / "snapshot.html").write_text(
        """
        <table class="items"><tbody><tr class="odd theme6">
          <td class="zentriert rueckennummer bg_Torwart" title="Kaleci">1</td>
          <td class="posrela"><table class="inline-table">
            <tr><td class="hauptlink"><a href="/p/profil/spieler/7">Player One</a></td></tr>
            <tr><td>Kaleci</td></tr>
          </table></td>
          <td class="zentriert">25</td><td class="zentriert"><img title="Türkiye"></td>
          <td class="zentriert">2028</td><td class="rechts hauptlink">€4m</td>
        </tr></tbody></table>
        """,
        encoding="utf-8",
    )
    state = tmp_path / "state.json"
    changes = tmp_path / "changes.json"

    result = CliRunner().invoke(
        app,
        [
            "update-current-changes",
            "--league-page",
            str(league_page),
            "--raw-dir",
            str(tmp_path / "raw"),
            "--state",
            str(state),
            "--output",
            str(changes),
        ],
    )

    assert result.exit_code == 0, result.output
    assert len(json.loads(state.read_text(encoding="utf-8"))) == 1
    assert json.loads(changes.read_text(encoding="utf-8"))["observation_count"] == 1


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


def test_refresh_dashboard_uses_explicit_live_source_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = tmp_path / "candidate.json"
    candidate.write_text(
        '{"schema_version":1,"freshness":{"source_status":"stale"}}',
        encoding="utf-8",
    )
    tff_page = Path(__file__).parent / "fixtures" / "tff" / "super_lig_fixture.html"
    squad_page = tmp_path / "league.html"
    squad_page.write_text("<html>fresh league snapshot</html>", encoding="utf-8")
    output = tmp_path / "dashboard.json"
    unavailable = ProviderBatch(
        "test-api",
        "TSL",
        "2026-27",
        "",
        (),
        available=False,
        reason="test",
    )
    monkeypatch.setattr(cli_module, "fetch_football_data_matches", lambda season: unavailable)
    monkeypatch.setattr(cli_module, "fetch_sportsdb_events", lambda season: unavailable)

    result = CliRunner().invoke(
        app,
        [
            "refresh-dashboard",
            "--candidate",
            str(candidate),
            "--tff-page",
            str(tff_page),
            "--squad-page",
            str(squad_page),
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["freshness"]["source_status"] == "fresh"
    assert "Official TFF fixture snapshot" in payload["freshness"]["source_notes"][0]


def test_refresh_dashboard_preserves_dated_market_fallback_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = tmp_path / "candidate.json"
    candidate.write_text('{"schema_version":1}', encoding="utf-8")
    tff_page = Path(__file__).parent / "fixtures" / "tff" / "super_lig_fixture.html"
    squad_snapshot = tmp_path / "squads.json"
    squad_snapshot.write_text('{"current_squads":[]}', encoding="utf-8")
    output = tmp_path / "dashboard.json"
    unavailable = ProviderBatch(
        "test-api",
        "TSL",
        "2026-27",
        "",
        (),
        available=False,
        reason="test",
    )
    monkeypatch.setattr(cli_module, "fetch_football_data_matches", lambda season: unavailable)
    monkeypatch.setattr(cli_module, "fetch_sportsdb_events", lambda season: unavailable)

    result = CliRunner().invoke(
        app,
        [
            "refresh-dashboard",
            "--candidate",
            str(candidate),
            "--tff-page",
            str(tff_page),
            "--squad-page",
            str(squad_snapshot),
            "--squad-snapshot-at",
            "2026-07-23T07:45:09.809421+00:00",
            "--market-source-note",
            "Live market refresh unavailable; dated valuation snapshot retained.",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    freshness = json.loads(output.read_text(encoding="utf-8"))["freshness"]
    assert freshness["squad_snapshot_at"] == "2026-07-23T07:45:09.809421+00:00"
    assert freshness["valuation_snapshot_at"] == "2026-07-23T07:45:09.809421+00:00"
    assert freshness["source_notes"][1] == (
        "Live market refresh unavailable; dated valuation snapshot retained."
    )


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
