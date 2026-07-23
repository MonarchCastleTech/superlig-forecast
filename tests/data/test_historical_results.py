from pathlib import Path
from zipfile import ZipFile

import duckdb

from superlig_forecast.data.historical_results import extract_historical_results_archive
from superlig_forecast.data.warehouse import Warehouse


def test_extract_historical_results_archive(tmp_path: Path) -> None:
    archive = tmp_path / "history.zip"
    with ZipFile(archive, "w") as payload:
        payload.writestr("all_euro_data.csv", "Div,Date\nT1,13/08/06\n")

    extracted = extract_historical_results_archive(archive, tmp_path / "processed")

    assert extracted.read_text(encoding="utf-8").startswith("Div,Date")


def test_load_historical_turkish_results_and_odds(tmp_path: Path) -> None:
    source = tmp_path / "all_euro_data.csv"
    source.write_text(
        "Div,Date,Time,HomeTeam,AwayTeam,FTHG,FTAG,FTR,MaxA,AvgH,AvgD,AvgA\n"
        "T1,13/08/06,Alpha,Beta,2,1,H,,1.80,3.40,4.50\n"
        "T1,20/08/06,15:00,Beta,Alpha,0,0,D,,2.10,3.10,3.20\n"
        "T1,27/08/06,15:00,Broken,Row,2,A,H,,2.10,3.10,3.20\n"
        "E0,13/08/06,15:00,Other,Else,0,0,D,,2.00,3.00,3.50\n",
        encoding="utf-8",
    )
    path = tmp_path / "model.duckdb"
    warehouse = Warehouse(path)
    warehouse.build([])
    with duckdb.connect(str(path)) as connection:
        connection.execute(
            """
            create or replace table matches(
                game_id integer,
                competition_id varchar,
                season integer,
                date date,
                home_club_name varchar,
                away_club_name varchar,
                home_club_goals integer,
                away_club_goals integer
            )
            """
        )
        connection.execute(
            """
            insert into matches values
            (99, 'TR1', 2025, '2026-05-01', 'Gamma', 'Delta', 1, 0)
            """
        )

    counts = warehouse.load_historical_results_csv(source)
    training_count = warehouse.refresh_training_matches()

    assert counts == {"historical_matches": 2, "odds": 2}
    assert training_count == 3
    with duckdb.connect(str(path), read_only=True) as connection:
        row = connection.execute(
            """
            select season, home_team, away_team, home_goals, away_goals,
                   home_odds, draw_odds, away_odds
            from historical_matches join odds using (match_id)
            """
        ).fetchone()
        training_odds = connection.execute(
            """
            select home_odds, draw_odds, away_odds
            from training_matches
            where source = 'football-data'
            limit 1
            """
        ).fetchone()
    assert row == (2006, "Alpha", "Beta", 2, 1, 1.8, 3.4, 4.5)
    assert training_odds == (None, None, None)
