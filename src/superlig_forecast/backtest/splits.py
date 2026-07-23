"""Expanding walk-forward season splits."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BacktestFold:
    train_seasons: tuple[str, ...]
    test_season: str


def walk_forward_folds(seasons: list[str], warmup_end: str) -> list[BacktestFold]:
    folds = [
        BacktestFold(tuple(item for item in seasons if item < season), season)
        for season in seasons
        if season > warmup_end
    ]
    if len(folds) != 20:
        raise ValueError(f"expected 20 scored folds, found {len(folds)}")
    return folds

