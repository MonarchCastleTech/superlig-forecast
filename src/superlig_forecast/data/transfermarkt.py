"""Adapter for the public structured Transfermarkt-derived DuckDB dataset."""

from pathlib import Path
from types import TracebackType
from typing import cast

import duckdb
import polars as pl
from pydantic import BaseModel, ConfigDict

REQUIRED_TABLES = frozenset(
    {"players", "player_valuations", "transfers", "appearances", "games", "game_lineups"}
)
TURKISH_COMPETITIONS = ("TR1", "TR2", "TR3", "TR4", "TRC")


class DatasetManifest(BaseModel):
    """Coverage and output summary for one export."""

    model_config = ConfigDict(frozen=True)

    requested_competitions: tuple[str, ...]
    missing_competitions: tuple[str, ...]
    exported_tables: tuple[str, ...]


class TransfermarktAdapter:
    """Reads curated football entities from a DuckDB snapshot."""

    def __init__(self, database: Path) -> None:
        self.connection = duckdb.connect(str(database), read_only=True)
        self._validate_schema()

    def __enter__(self) -> "TransfermarktAdapter":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.connection.close()

    def _validate_schema(self) -> None:
        present = {row[0] for row in self.connection.execute("show tables").fetchall()}
        missing = REQUIRED_TABLES - present
        if missing:
            raise ValueError(f"Transfermarkt snapshot missing tables: {sorted(missing)}")

    def _read(self, query: str) -> pl.DataFrame:
        return cast(pl.DataFrame, pl.from_arrow(self.connection.execute(query).arrow()))

    def read_players(self) -> pl.DataFrame:
        return self._read("select * from players order by player_id")

    def read_valuations(self) -> pl.DataFrame:
        return self._read(
            """
            select player_id, date, market_value_in_eur as market_value_eur,
                   current_club_id, player_club_domestic_competition_id as competition_id
            from player_valuations
            order by player_id, date
            """
        )

    def read_transfers(self) -> pl.DataFrame:
        return self._read("select * from transfers order by player_id, transfer_date")

    def read_appearances(self) -> pl.DataFrame:
        return self._read("select * from appearances order by game_id, player_id")

    def read_lineups(self) -> pl.DataFrame:
        return self._read("select * from game_lineups order by game_id, player_id")

    def read_games(self) -> pl.DataFrame:
        return self._read("select * from games order by game_id")

    def export_turkish_pyramid(self, output_dir: Path) -> DatasetManifest:
        """Export available Turkish competition rows and report gaps."""

        output_dir.mkdir(parents=True, exist_ok=True)
        games = self.read_games().filter(pl.col("competition_id").is_in(TURKISH_COMPETITIONS))
        valuations = self.read_valuations().filter(
            pl.col("competition_id").is_in(TURKISH_COMPETITIONS)
        )
        players = self.read_players()
        games.write_parquet(output_dir / "games.parquet")
        valuations.write_parquet(output_dir / "player_valuations.parquet")
        players.write_parquet(output_dir / "players.parquet")
        present = set(games["competition_id"].to_list()) | set(
            valuations["competition_id"].drop_nulls().to_list()
        )
        return DatasetManifest(
            requested_competitions=TURKISH_COMPETITIONS,
            missing_competitions=tuple(item for item in TURKISH_COMPETITIONS if item not in present),
            exported_tables=("games", "player_valuations", "players"),
        )
