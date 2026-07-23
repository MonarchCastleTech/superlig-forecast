"""Strict season-by-season evaluation on normalized historical matches."""

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import duckdb
import numpy as np
import numpy.typing as npt

from superlig_forecast.backtest.metrics import brier_score_multiclass
from superlig_forecast.modeling.market import remove_margin
from superlig_forecast.modeling.team_strength import PlayedMatch, TeamStrengthModel


@dataclass(frozen=True)
class BacktestMatch:
    date: date
    season: int
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    home_odds: float | None = None
    draw_odds: float | None = None
    away_odds: float | None = None

    @property
    def target(self) -> int:
        if self.home_goals > self.away_goals:
            return 0
        if self.home_goals == self.away_goals:
            return 1
        return 2

    def played(self) -> PlayedMatch:
        return PlayedMatch(
            self.date,
            self.season,
            self.home_team,
            self.away_team,
            self.home_goals,
            self.away_goals,
        )

    def market_probabilities(self) -> npt.NDArray[np.float64] | None:
        values = (self.home_odds, self.draw_odds, self.away_odds)
        if any(value is None or value <= 1.0 for value in values):
            return None
        return remove_margin(np.asarray(values, dtype=float))


@dataclass(frozen=True)
class ScoreSummary:
    naive_log_loss: float
    naive_brier: float
    structural_log_loss: float
    structural_brier: float
    hybrid_log_loss: float
    hybrid_brier: float
    market_log_loss: float | None
    market_brier: float | None
    market_subset_hybrid_log_loss: float | None
    market_subset_hybrid_brier: float | None
    hybrid_accuracy: float


@dataclass(frozen=True)
class FoldSummary:
    season: int
    match_count: int
    market_match_count: int
    scores: ScoreSummary


@dataclass(frozen=True)
class BacktestReport:
    folds: tuple[FoldSummary, ...]
    aggregate: ScoreSummary
    match_count: int
    market_match_count: int

    @property
    def fold_count(self) -> int:
        return len(self.folds)


def load_backtest_matches(path: Path) -> list[BacktestMatch]:
    """Read the source-prioritized analytical match table."""

    with duckdb.connect(str(path), read_only=True) as connection:
        rows = connection.execute(
            """
            select date, season, home_team, away_team, home_goals, away_goals,
                   home_odds, draw_odds, away_odds
            from training_matches
            order by date, match_id
            """
        ).fetchall()
    return [
        BacktestMatch(
            match_date,
            int(season),
            home_team,
            away_team,
            int(home_goals),
            int(away_goals),
            float(home_odds) if home_odds is not None else None,
            float(draw_odds) if draw_odds is not None else None,
            float(away_odds) if away_odds is not None else None,
        )
        for (
            match_date,
            season,
            home_team,
            away_team,
            home_goals,
            away_goals,
            home_odds,
            draw_odds,
            away_odds,
        ) in rows
    ]


def _log_loss(probabilities: npt.NDArray[np.float64], targets: npt.NDArray[np.int64]) -> float:
    selected = probabilities[np.arange(targets.size), targets]
    return float(-np.mean(np.log(np.clip(selected, 1e-12, 1.0))))


def _score(
    naive: npt.NDArray[np.float64],
    structural: npt.NDArray[np.float64],
    hybrid: npt.NDArray[np.float64],
    targets: npt.NDArray[np.int64],
    market: npt.NDArray[np.float64] | None,
    market_targets: npt.NDArray[np.int64] | None,
    market_hybrid: npt.NDArray[np.float64] | None,
) -> ScoreSummary:
    return ScoreSummary(
        naive_log_loss=_log_loss(naive, targets),
        naive_brier=brier_score_multiclass(naive, targets),
        structural_log_loss=_log_loss(structural, targets),
        structural_brier=brier_score_multiclass(structural, targets),
        hybrid_log_loss=_log_loss(hybrid, targets),
        hybrid_brier=brier_score_multiclass(hybrid, targets),
        market_log_loss=(
            _log_loss(market, market_targets)
            if market is not None and market_targets is not None
            else None
        ),
        market_brier=(
            brier_score_multiclass(market, market_targets)
            if market is not None and market_targets is not None
            else None
        ),
        market_subset_hybrid_log_loss=(
            _log_loss(market_hybrid, market_targets)
            if market_hybrid is not None and market_targets is not None
            else None
        ),
        market_subset_hybrid_brier=(
            brier_score_multiclass(market_hybrid, market_targets)
            if market_hybrid is not None and market_targets is not None
            else None
        ),
        hybrid_accuracy=float(np.mean(np.argmax(hybrid, axis=1) == targets)),
    )


def run_walk_forward(
    matches: list[BacktestMatch],
    *,
    start_season: int,
    end_season: int,
    market_weight: float = 0.9,
) -> BacktestReport:
    """Fit only on earlier seasons and score every requested test season."""

    folds: list[FoldSummary] = []
    all_naive: list[npt.NDArray[np.float64]] = []
    all_structural: list[npt.NDArray[np.float64]] = []
    all_hybrid: list[npt.NDArray[np.float64]] = []
    all_targets: list[int] = []
    all_market: list[npt.NDArray[np.float64]] = []
    all_market_hybrid: list[npt.NDArray[np.float64]] = []
    all_market_targets: list[int] = []
    for season in range(start_season, end_season + 1):
        training = [match for match in matches if match.season < season]
        test = [match for match in matches if match.season == season]
        if not training or not test:
            raise ValueError(f"season {season} lacks strict train/test coverage")
        model = TeamStrengthModel.fit([match.played() for match in training], before_season=season)
        target_counts = np.bincount(
            np.asarray([match.target for match in training], dtype=np.int64),
            minlength=3,
        ).astype(float)
        naive_row = (target_counts + 1.0) / (target_counts.sum() + 3.0)
        naive = np.tile(naive_row, (len(test), 1))
        structural = np.vstack(
            [model.predict_one_x_two(match.home_team, match.away_team) for match in test]
        )
        hybrid = structural.copy()
        fold_market: list[npt.NDArray[np.float64]] = []
        fold_market_hybrid: list[npt.NDArray[np.float64]] = []
        fold_market_targets: list[int] = []
        for index, match in enumerate(test):
            market = match.market_probabilities()
            if market is None:
                continue
            hybrid[index] = (1.0 - market_weight) * structural[index] + market_weight * market
            hybrid[index] /= hybrid[index].sum()
            fold_market.append(market)
            fold_market_hybrid.append(hybrid[index])
            fold_market_targets.append(match.target)
        targets = np.asarray([match.target for match in test], dtype=np.int64)
        market_array = np.vstack(fold_market) if fold_market else None
        market_targets = (
            np.asarray(fold_market_targets, dtype=np.int64) if fold_market_targets else None
        )
        market_hybrid = np.vstack(fold_market_hybrid) if fold_market_hybrid else None
        scores = _score(
            naive,
            structural,
            hybrid,
            targets,
            market_array,
            market_targets,
            market_hybrid,
        )
        folds.append(FoldSummary(season, len(test), len(fold_market), scores))
        all_naive.extend(naive)
        all_structural.extend(structural)
        all_hybrid.extend(hybrid)
        all_targets.extend(targets.tolist())
        all_market.extend(fold_market)
        all_market_hybrid.extend(fold_market_hybrid)
        all_market_targets.extend(fold_market_targets)
    target_array = np.asarray(all_targets, dtype=np.int64)
    market_array = np.vstack(all_market) if all_market else None
    market_targets = np.asarray(all_market_targets, dtype=np.int64) if all_market_targets else None
    market_hybrid = np.vstack(all_market_hybrid) if all_market_hybrid else None
    aggregate = _score(
        np.vstack(all_naive),
        np.vstack(all_structural),
        np.vstack(all_hybrid),
        target_array,
        market_array,
        market_targets,
        market_hybrid,
    )
    return BacktestReport(
        tuple(folds),
        aggregate,
        len(all_targets),
        len(all_market_targets),
    )
