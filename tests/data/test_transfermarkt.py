from pathlib import Path

import duckdb

from superlig_forecast.data.transfermarkt import TransfermarktAdapter

SCHEMA = Path(__file__).parents[1] / "fixtures" / "transfermarkt" / "schema.sql"


def build_database(path: Path) -> None:
    with duckdb.connect(str(path)) as connection:
        connection.execute(SCHEMA.read_text(encoding="utf-8"))


def test_valuation_keeps_effective_date_and_club(tmp_path: Path) -> None:
    database = tmp_path / "sample.duckdb"
    build_database(database)

    with TransfermarktAdapter(database) as adapter:
        rows = adapter.read_valuations()

    assert rows["player_id"].item() == 10
    assert rows["date"].item().isoformat() == "2025-07-01"
    assert rows["market_value_eur"].item() == 12_000_000
    assert rows["current_club_id"].item() == 1


def test_export_reports_missing_lower_competitions(tmp_path: Path) -> None:
    database = tmp_path / "sample.duckdb"
    output = tmp_path / "export"
    build_database(database)

    with TransfermarktAdapter(database) as adapter:
        manifest = adapter.export_turkish_pyramid(output)

    assert set(manifest.requested_competitions) == {"TR1", "TR2", "TR3", "TR4", "TRC"}
    assert manifest.missing_competitions == ("TR2", "TR3", "TR4", "TRC")
    assert (output / "player_valuations.parquet").exists()
