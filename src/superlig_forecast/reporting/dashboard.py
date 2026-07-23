"""Static data contract for the interactive forecast dashboard."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Literal, cast, overload

import orjson


def _rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Dashboard source artifact is missing: {path}")
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@overload
def _number(
    row: dict[str, str],
    key: str,
    *,
    integer: bool = False,
    nullable: Literal[False] = False,
) -> int | float: ...


@overload
def _number(
    row: dict[str, str],
    key: str,
    *,
    integer: bool = False,
    nullable: Literal[True],
) -> int | float | None: ...


def _number(
    row: dict[str, str],
    key: str,
    *,
    integer: bool = False,
    nullable: bool = False,
) -> int | float | None:
    raw = row.get(key)
    if raw is None or raw.strip() == "":
        if nullable:
            return None
        raise ValueError(f"{key} is missing")
    try:
        return int(float(raw)) if integer else float(raw)
    except ValueError as exc:
        raise ValueError(f"{key} must be numeric, got {raw!r}") from exc


def _probability(row: dict[str, str], key: str) -> float:
    value = float(_number(row, key))
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{key} must be between 0 and 1, got {value}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Dashboard source artifact is missing: {path}")
    value = orjson.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def build_dashboard_payload(
    forecast_dir: Path,
    backtest_path: Path,
    position_backtest_path: Path,
) -> dict[str, Any]:
    """Normalize engine artifacts into the versioned web dashboard contract."""

    manifest = _load_json(forecast_dir / "manifest.json")
    backtest = _load_json(backtest_path)
    position_backtest = _load_json(position_backtest_path)

    championship = [
        {
            "club": row["club"],
            "squad_value_eur": _number(
                row,
                "squad_value_eur",
                integer=True,
                nullable=True,
            ),
            "champion_count": _number(row, "champion_count", integer=True),
            "champion_probability": _probability(row, "champion_probability"),
            "ci95_half_width": _probability(row, "ci95_half_width"),
        }
        for row in _rows(forecast_dir / "champion-probabilities.csv")
    ]
    championship.sort(
        key=lambda row: cast(float, row["champion_probability"]),
        reverse=True,
    )

    convergence = [
        {
            "simulation_count": _number(row, "simulation_count", integer=True),
            "club": row["club_id"],
            "champion_probability": _probability(row, "champion_probability"),
        }
        for row in _rows(forecast_dir / "championship-convergence.csv")
    ]
    convergence.sort(key=lambda row: (int(row["simulation_count"]), str(row["club"])))

    fixtures = [
        {
            "home_team": row["home_team"],
            "away_team": row["away_team"],
            "home_expected_goals": _number(row, "home_expected_goals"),
            "away_expected_goals": _number(row, "away_expected_goals"),
            "home_win_probability": _probability(row, "home_win_probability"),
            "draw_probability": _probability(row, "draw_probability"),
            "away_win_probability": _probability(row, "away_win_probability"),
        }
        for row in _rows(forecast_dir / "fixture-expectations.csv")
    ]
    positions = [
        {
            "club": row["club"],
            "position": _number(row, "position", integer=True),
            "count": _number(row, "count", integer=True),
            "probability": _probability(row, "probability"),
        }
        for row in _rows(forecast_dir / "position-probabilities.csv")
    ]
    positions.sort(key=lambda row: (str(row["club"]), int(row["position"])))
    expected_standings = [
        {
            "club": row["club"],
            "expected_position": _number(row, "expected_position"),
            "median_position": _number(row, "median_position", integer=True),
            "most_likely_position": _number(
                row,
                "most_likely_position",
                integer=True,
            ),
            "expected_points": _number(row, "expected_points"),
            "expected_goal_difference": _number(
                row,
                "expected_goal_difference",
            ),
            "top_four_probability": _probability(row, "top_four_probability"),
            "position_17_probability": _number(
                row,
                "position_17_probability",
                nullable=True,
            ),
            "relegation_probability": _probability(
                row,
                "relegation_probability",
            ),
        }
        for row in _rows(forecast_dir / "expected-standings.csv")
    ]
    expected_standings.sort(key=lambda row: cast(float, row["expected_position"]))

    return {
        "schema_version": 1,
        "meta": {
            "season": manifest["season"],
            "simulations": int(manifest["n_simulations"]),
            "seed": int(manifest["seed"]),
            "model_version": manifest["model_version"],
            "team_count": int(manifest["team_count"]),
            "fixture_count": int(manifest["fixture_count"]),
            "checkpoints": [int(value) for value in manifest["checkpoints"]],
            "value_coefficient": float(manifest["value_coefficient"]),
            "source_alignment": manifest.get("team_source_alignment"),
        },
        "championship": championship,
        "convergence": convergence,
        "fixtures": fixtures,
        "positions": positions,
        "expected_standings": expected_standings,
        "backtest": {
            key: backtest[key]
            for key in (
                "method",
                "start_season",
                "end_season",
                "market_weight",
                "fold_count",
                "match_count",
                "market_match_count",
                "aggregate",
                "folds",
                "acceptance",
            )
        },
        "position_backtest": {
            key: position_backtest[key]
            for key in (
                "method",
                "start_season",
                "end_season",
                "fold_count",
                "simulations_per_fold",
                "aggregate",
                "folds",
                "acceptance",
            )
        },
    }
