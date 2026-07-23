"""Historical bookmaker-odds normalization."""

import csv
from datetime import datetime
from pathlib import Path

import polars as pl

from superlig_forecast.domain import OddsObservation

PROVIDERS = {
    "Bet365": ("B365H", "B365D", "B365A"),
    "Pinnacle": ("PSH", "PSD", "PSA"),
    "Average": ("AvgH", "AvgD", "AvgA"),
}


class OddsAdapter:
    """Converts wide football odds archives to provider observations."""

    def read(self, path: Path, observed_at: datetime | None) -> pl.DataFrame:
        """Read a CSV while preserving its documented observation time."""

        if observed_at is None:
            raise ValueError("observation timestamp is required for point-in-time odds")
        records: list[dict[str, object]] = []
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                match_key = f"{row['Date']}|{row['HomeTeam']}|{row['AwayTeam']}"
                for provider, columns in PROVIDERS.items():
                    values = tuple(row.get(column, "") for column in columns)
                    if any(value in {"", None} for value in values):
                        continue
                    observation = OddsObservation(
                        match_source_key=match_key,
                        provider=provider,
                        observed_at=observed_at,
                        home_odds=float(values[0]),
                        draw_odds=float(values[1]),
                        away_odds=float(values[2]),
                    )
                    records.append(observation.model_dump(mode="python"))
        return pl.DataFrame(records)
