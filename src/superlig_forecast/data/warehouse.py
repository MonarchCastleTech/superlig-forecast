"""Canonical DuckDB schema and deterministic build manifests."""

import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import duckdb
import orjson
from pydantic import BaseModel, ConfigDict

WAREHOUSE_TABLES = (
    "competitions",
    "clubs",
    "club_aliases",
    "players",
    "current_players",
    "player_aliases",
    "matches",
    "historical_matches",
    "oddsportal_matches",
    "training_matches",
    "lineups",
    "appearances",
    "valuations",
    "transfers",
    "odds",
    "raw_manifests",
    "coverage",
)


def _table_count(connection: duckdb.DuckDBPyConnection, table: str) -> int:
    row = connection.execute(f"select count(*) from {table}").fetchone()
    if row is None:
        raise RuntimeError(f"count query returned no row for {table}")
    return int(row[0])


class BuildManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    data_hash: str
    table_count: int


class Warehouse:
    """Creates the stable analytical schema."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def build(self, snapshot_manifests: list[Any]) -> BuildManifest:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(self.path)) as connection:
            for table in WAREHOUSE_TABLES:
                connection.execute(f"create table if not exists {table}(record_id varchar)")
        payload = orjson.dumps(snapshot_manifests, option=orjson.OPT_SORT_KEYS, default=str)
        return BuildManifest(
            data_hash=hashlib.sha256(payload).hexdigest(),
            table_count=len(WAREHOUSE_TABLES),
        )

    def tables(self) -> list[str]:
        with duckdb.connect(str(self.path), read_only=True) as connection:
            return [row[0] for row in connection.execute("show tables").fetchall()]

    def load_transfermarkt_csvs(self, csv_paths: Mapping[str, Path]) -> dict[str, int]:
        """Replace canonical source tables with inferred Transfermarkt CSV data."""

        counts: dict[str, int] = {}
        with duckdb.connect(str(self.path)) as connection:
            for table, path in csv_paths.items():
                if table not in WAREHOUSE_TABLES:
                    raise ValueError(f"unsupported warehouse table: {table}")
                connection.execute(
                    f"""
                    create or replace table {table} as
                    select * from read_csv_auto(
                        ?, header = true, sample_size = -1, null_padding = true
                    )
                    """,
                    [str(path)],
                )
                counts[table] = _table_count(connection, table)
        return counts

    def load_historical_results_csv(self, csv_path: Path) -> dict[str, int]:
        """Load Football-Data style Turkish results and consensus 1X2 odds."""

        with duckdb.connect(str(self.path)) as connection:
            connection.execute(
                """
                create or replace temporary table football_data_raw as
                select
                    *,
                    case
                        when regexp_matches(
                            trim(cast(Date as varchar)),
                            '^\\d{1,2}/\\d{1,2}/\\d{2}$'
                        )
                        then try_strptime(cast(Date as varchar), '%d/%m/%y')::date
                        else try_strptime(
                            cast(Date as varchar),
                            ['%d/%m/%Y', '%Y-%m-%d']
                        )::date
                    end as match_date
                from read_csv_auto(
                    ?, header = true, sample_size = -1, null_padding = true,
                    all_varchar = true, strict_mode = false
                )
                where Div = 'T1'
                """,
                [str(csv_path)],
            )
            connection.execute(
                """
                create or replace temporary table football_data_t1 as
                select
                    match_date,
                    case
                        when not regexp_matches(
                            coalesce(Time, ''), '^\\d{1,2}:\\d{2}'
                        )
                        then Time else HomeTeam
                    end as normalized_home_team,
                    case
                        when not regexp_matches(
                            coalesce(Time, ''), '^\\d{1,2}:\\d{2}'
                        )
                        then HomeTeam else AwayTeam
                    end as normalized_away_team,
                    case
                        when not regexp_matches(
                            coalesce(Time, ''), '^\\d{1,2}:\\d{2}'
                        )
                        then AwayTeam else FTHG
                    end as normalized_home_goals,
                    case
                        when not regexp_matches(
                            coalesce(Time, ''), '^\\d{1,2}:\\d{2}'
                        )
                        then FTHG else FTAG
                    end as normalized_away_goals,
                    case
                        when not regexp_matches(
                            coalesce(Time, ''), '^\\d{1,2}:\\d{2}'
                        )
                        then MaxA else AvgH
                    end as normalized_home_odds,
                    case
                        when not regexp_matches(
                            coalesce(Time, ''), '^\\d{1,2}:\\d{2}'
                        )
                        then AvgH else AvgD
                    end as normalized_draw_odds,
                    case
                        when not regexp_matches(
                            coalesce(Time, ''), '^\\d{1,2}:\\d{2}'
                        )
                        then AvgD else AvgA
                    end as normalized_away_odds
                from football_data_raw
                """
            )
            connection.execute(
                """
                create or replace table historical_matches as
                select
                    md5(concat_ws(
                        '|', cast(match_date as varchar),
                        normalized_home_team, normalized_away_team
                    )) as match_id,
                    match_date as date,
                    year(match_date)
                        - case when month(match_date) < 7 then 1 else 0 end as season,
                    normalized_home_team as home_team,
                    normalized_away_team as away_team,
                    try_cast(normalized_home_goals as integer) as home_goals,
                    try_cast(normalized_away_goals as integer) as away_goals
                from football_data_t1
                where match_date is not null
                  and try_cast(normalized_home_goals as integer) is not null
                  and try_cast(normalized_away_goals as integer) is not null
                """
            )
            connection.execute(
                """
                create or replace table odds as
                select
                    md5(concat_ws(
                        '|', cast(match_date as varchar),
                        normalized_home_team, normalized_away_team
                    )) as match_id,
                    try_cast(normalized_home_odds as double) as home_odds,
                    try_cast(normalized_draw_odds as double) as draw_odds,
                    try_cast(normalized_away_odds as double) as away_odds
                from football_data_t1
                where match_date is not null
                  and try_cast(normalized_home_goals as integer) is not null
                  and try_cast(normalized_away_goals as integer) is not null
                """
            )
            return {
                table: _table_count(connection, table) for table in ("historical_matches", "odds")
            }

    def refresh_training_matches(self, *, use_oddsportal: bool = False) -> int:
        """Materialize one continuous, source-prioritized Süper Lig match table."""

        historical_cutoff = 2007 if use_oddsportal else 2020
        oddsportal_union = (
            """
                union all

                select
                    match_id,
                    date,
                    season,
                    home_team,
                    away_team,
                    home_goals,
                    away_goals,
                    home_odds,
                    draw_odds,
                    away_odds,
                    'oddsportal' as source
                from oddsportal_matches
                where season between 2008 and 2020
            """
            if use_oddsportal
            else ""
        )
        with duckdb.connect(str(self.path)) as connection:
            connection.execute(
                f"""
                create or replace table training_matches as
                select
                    h.match_id,
                    h.date,
                    h.season,
                    h.home_team,
                    h.away_team,
                    h.home_goals,
                    h.away_goals,
                    null::double as home_odds,
                    null::double as draw_odds,
                    null::double as away_odds,
                    'football-data' as source
                from historical_matches h
                where h.season <= {historical_cutoff}

                {oddsportal_union}

                union all

                select
                    cast(game_id as varchar) as match_id,
                    date,
                    season,
                    home_club_name as home_team,
                    away_club_name as away_team,
                    home_club_goals as home_goals,
                    away_club_goals as away_goals,
                    null::double as home_odds,
                    null::double as draw_odds,
                    null::double as away_odds,
                    'transfermarkt' as source
                from matches
                where competition_id = 'TR1'
                  and season >= 2021
                  and home_club_goals is not null
                  and away_club_goals is not null
                """
            )
            return _table_count(connection, "training_matches")

    def load_oddsportal_csvs(self, csv_paths: Mapping[str, Path]) -> int:
        """Load consistently shaped Turkish top-flight results and 1X2 odds."""

        with duckdb.connect(str(self.path)) as connection:
            connection.execute(
                """
                create or replace temporary table oddsportal_leagues as
                select * from read_csv_auto(
                    ?, header = true, all_varchar = true, sample_size = -1
                )
                """,
                [str(csv_paths["leagues"])],
            )
            connection.execute(
                """
                create or replace temporary table oddsportal_raw_matches as
                select * from read_csv_auto(
                    ?, header = true, all_varchar = true, sample_size = -1
                )
                """,
                [str(csv_paths["matches"])],
            )
            connection.execute(
                """
                create or replace table oddsportal_matches as
                select
                    'oddsportal-' || m.id as match_id,
                    to_timestamp(try_cast(m.timestamp as double))::date as date,
                    try_cast(
                        regexp_extract(l.name, 'super-lig-(\\d{4})-', 1) as integer
                    ) as season,
                    m.home as home_team,
                    m.away as away_team,
                    try_cast(m.score_h as integer) as home_goals,
                    try_cast(m.score_a as integer) as away_goals,
                    try_cast(m.m_o1 as double) as home_odds,
                    try_cast(m.m_oX as double) as draw_odds,
                    try_cast(m.m_o2 as double) as away_odds
                from oddsportal_raw_matches m
                join oddsportal_leagues l on m.liga_id = l.id
                where lower(l.country) = 'turkey'
                  and regexp_matches(l.name, '^super-lig-\\d{4}-\\d{4}$')
                  and try_cast(m.score_h as integer) is not null
                  and try_cast(m.score_a as integer) is not null
                """
            )
            return _table_count(connection, "oddsportal_matches")

    def load_current_players_parquet(self, parquet_path: Path) -> int:
        """Replace the live current-player table from a normalized Parquet artifact."""

        with duckdb.connect(str(self.path)) as connection:
            connection.execute(
                """
                create or replace table current_players as
                select * from read_parquet(?)
                """,
                [str(parquet_path)],
            )
            return _table_count(connection, "current_players")
