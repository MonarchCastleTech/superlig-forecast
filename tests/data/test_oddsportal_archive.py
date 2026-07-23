from pathlib import Path
from zipfile import ZipFile

import duckdb

from superlig_forecast.data.oddsportal_archive import extract_oddsportal_archive
from superlig_forecast.data.warehouse import Warehouse


def test_extract_and_load_oddsportal_turkish_matches(tmp_path: Path) -> None:
    archive_path = tmp_path / "odds.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr(
            "leagues.csv",
            "id,country,name\n1,turkey,super-lig-2008-2009\n2,england,premier-league\n",
        )
        archive.writestr(
            "matches.csv",
            "id,timestamp,liga_id,home,away,score_h,score_a,m_o1,m_oX,m_o2\n"
            "10,1219449600,1,Alpha,Beta,2,1,1.80,3.40,4.50\n"
            "11,1219449600,2,Other,Else,1,1,2.00,3.00,3.50\n",
        )

    csv_paths = extract_oddsportal_archive(archive_path, tmp_path / "processed")
    warehouse_path = tmp_path / "model.duckdb"
    warehouse = Warehouse(warehouse_path)
    warehouse.build([])
    count = warehouse.load_oddsportal_csvs(csv_paths)
    with duckdb.connect(str(warehouse_path)) as connection:
        connection.execute(
            """
            create or replace table historical_matches as
            select 'h' match_id, date '2007-08-01' date, 2007 season,
                   'Old A' home_team, 'Old B' away_team, 1 home_goals, 0 away_goals
            """
        )
        connection.execute(
            """
            create or replace table odds as
            select 'h' match_id, 2.0 home_odds, 3.0 draw_odds, 4.0 away_odds
            """
        )
        connection.execute(
            """
            create or replace table matches as
            select 20 game_id, 'TR1' competition_id, 2021 season,
                   date '2022-05-01' date, 'New A' home_club_name,
                   'New B' away_club_name, 3 home_club_goals, 2 away_club_goals
            """
        )
    training_count = warehouse.refresh_training_matches(use_oddsportal=True)

    assert count == 1
    assert training_count == 3
    with duckdb.connect(str(warehouse_path), read_only=True) as connection:
        row = connection.execute(
            """
            select season, home_team, away_team, home_goals, away_goals,
                   home_odds, draw_odds, away_odds
            from oddsportal_matches
            """
        ).fetchone()
        sources = connection.execute(
            "select source, count(*) from training_matches group by source order by source"
        ).fetchall()
    assert row == (2008, "Alpha", "Beta", 2, 1, 1.8, 3.4, 4.5)
    assert sources == [
        ("football-data", 1),
        ("oddsportal", 1),
        ("transfermarkt", 1),
    ]
