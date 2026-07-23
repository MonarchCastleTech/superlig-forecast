from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import duckdb

from superlig_forecast.data.transfermarkt_archive import (
    TRANSFERMARKT_CSV_TABLES,
    extract_transfermarkt_archive,
)
from superlig_forecast.data.warehouse import Warehouse


def _write_fixture_archive(path: Path) -> None:
    fixtures = {
        "competitions.csv": "competition_id,name\nTR1,super-lig\n",
        "clubs.csv": "club_id,name,domestic_competition_id\n1,Alpha,TR1\n",
        "games.csv": (
            "game_id,competition_id,season,date,home_club_id,away_club_id,"
            "home_club_goals,away_club_goals\n"
            "10,TR1,2025,2026-05-01,1,2,2,1\n"
        ),
        "players.csv": "player_id,name,current_club_id\n100,Player One,1\n",
        "player_valuations.csv": (
            "player_id,date,market_value_in_eur,current_club_id\n100,2026-04-01,5000000,1\n"
        ),
        "appearances.csv": "appearance_id,game_id,player_id,minutes_played\nx,10,100,90\n",
        "game_lineups.csv": "game_lineups_id,game_id,player_id,club_id,type\nl,10,100,1,starting_lineup\n",
        "transfers.csv": "player_id,transfer_date,from_club_id,to_club_id\n100,2026-01-01,2,1\n",
    }
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        for name, content in fixtures.items():
            archive.writestr(name, content)


def test_extract_and_load_transfermarkt_archive(tmp_path: Path) -> None:
    archive = tmp_path / "transfermarkt.zip"
    _write_fixture_archive(archive)

    csv_paths = extract_transfermarkt_archive(archive, tmp_path / "csv")
    assert set(csv_paths) == set(TRANSFERMARKT_CSV_TABLES)

    warehouse_path = tmp_path / "model.duckdb"
    warehouse = Warehouse(warehouse_path)
    warehouse.build([])
    counts = warehouse.load_transfermarkt_csvs(csv_paths)

    assert counts["matches"] == 1
    assert counts["valuations"] == 1
    with duckdb.connect(str(warehouse_path), read_only=True) as connection:
        assert connection.execute("select competition_id from matches").fetchone() == ("TR1",)
