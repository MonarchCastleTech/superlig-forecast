"""Hierarchical priors for promoted clubs."""

from dataclasses import dataclass

import polars as pl


@dataclass(frozen=True)
class PromotionPrior:
    source_seasons: tuple[str, ...]
    division_offset: float

    @classmethod
    def fit(cls, history: pl.DataFrame, training_end: str) -> "PromotionPrior":
        past = history.filter(pl.col("season") <= training_end).sort("season")
        if past.is_empty():
            raise ValueError("promotion history is empty before training_end")
        mean = past["translation"].mean()
        if mean is None:
            raise ValueError("promotion history has no translation values")
        return cls(tuple(past["season"].to_list()), float(str(mean)))
