import csv
import json
from pathlib import Path

import pytest

from superlig_forecast.reporting.dashboard import build_dashboard_payload


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _artifact_set(tmp_path: Path) -> tuple[Path, Path, Path]:
    forecast = tmp_path / "forecast"
    forecast.mkdir()
    (forecast / "manifest.json").write_text(
        json.dumps(
            {
                "seed": 202627,
                "n_simulations": 50_000,
                "checkpoints": [10_000, 50_000],
                "season": "2026-27",
                "team_count": 2,
                "fixture_count": 1,
                "value_coefficient": 0.1,
                "team_source_alignment": {
                    "official_team_count": 2,
                    "market_team_count": 2,
                    "matched_team_count": 2,
                    "official_only": [],
                    "market_only": [],
                },
                "model_version": "0.1.0",
            }
        ),
        encoding="utf-8",
    )
    _write_csv(
        forecast / "champion-probabilities.csv",
        [
            {
                "club": "Fenerbahçe SK",
                "squad_value_eur": 333_150_000,
                "champion_count": 20_000,
                "champion_probability": 0.4,
                "ci95_half_width": 0.004,
            },
            {
                "club": "Galatasaray SK",
                "squad_value_eur": 323_300_000,
                "champion_count": 30_000,
                "champion_probability": 0.6,
                "ci95_half_width": 0.004,
            },
        ],
    )
    _write_csv(
        forecast / "championship-convergence.csv",
        [
            {
                "simulation_count": 10_000,
                "club_id": "Galatasaray SK",
                "champion_probability": 0.59,
            },
            {
                "simulation_count": 10_000,
                "club_id": "Fenerbahçe SK",
                "champion_probability": 0.41,
            },
            {
                "simulation_count": 50_000,
                "club_id": "Galatasaray SK",
                "champion_probability": 0.6,
            },
            {
                "simulation_count": 50_000,
                "club_id": "Fenerbahçe SK",
                "champion_probability": 0.4,
            },
        ],
    )
    _write_csv(
        forecast / "fixture-expectations.csv",
        [
            {
                "home_team": "Galatasaray SK",
                "away_team": "Fenerbahçe SK",
                "home_expected_goals": 1.6,
                "away_expected_goals": 1.3,
                "home_win_probability": 0.44,
                "draw_probability": 0.26,
                "away_win_probability": 0.3,
            }
        ],
    )
    _write_csv(
        forecast / "position-probabilities.csv",
        [
            {"club": "Galatasaray SK", "position": 1, "count": 30_000, "probability": 0.6},
            {"club": "Galatasaray SK", "position": 2, "count": 20_000, "probability": 0.4},
            {"club": "Fenerbahçe SK", "position": 1, "count": 20_000, "probability": 0.4},
            {"club": "Fenerbahçe SK", "position": 2, "count": 30_000, "probability": 0.6},
        ],
    )
    _write_csv(
        forecast / "expected-standings.csv",
        [
            {
                "club": "Galatasaray SK",
                "expected_position": 1.4,
                "median_position": 1,
                "most_likely_position": 1,
                "expected_points": 78.2,
                "expected_goal_difference": 42.1,
                "top_four_probability": 1.0,
                "position_17_probability": "",
                "relegation_probability": 0.0,
            },
            {
                "club": "Fenerbahçe SK",
                "expected_position": 1.6,
                "median_position": 2,
                "most_likely_position": 2,
                "expected_points": 76.4,
                "expected_goal_difference": 39.7,
                "top_four_probability": 1.0,
                "position_17_probability": "",
                "relegation_probability": 0.0,
            },
        ],
    )
    backtest = tmp_path / "backtest.json"
    backtest.write_text(
        json.dumps(
            {
                "method": "strict-expanding-window",
                "start_season": 2006,
                "end_season": 2025,
                "market_weight": 0.9,
                "fold_count": 20,
                "match_count": 6437,
                "market_match_count": 4074,
                "aggregate": {
                    "naive_log_loss": 1.0655,
                    "hybrid_log_loss": 1.0017,
                    "naive_brier": 0.6436,
                    "hybrid_brier": 0.5981,
                    "hybrid_accuracy": 0.514,
                },
                "folds": [
                    {
                        "season": 2025,
                        "match_count": 306,
                        "market_match_count": 0,
                        "scores": {
                            "naive_log_loss": 1.08,
                            "hybrid_log_loss": 1.01,
                        },
                    }
                ],
                "acceptance": {"passed": True, "checks": {"fold_count": True}},
            }
        ),
        encoding="utf-8",
    )
    position_backtest = tmp_path / "position-backtest.json"
    position_backtest.write_text(
        json.dumps(
            {
                "method": "strict-preseason-expanding-window-position-distribution",
                "start_season": 2006,
                "end_season": 2025,
                "fold_count": 20,
                "simulations_per_fold": 20_000,
                "aggregate": {
                    "position_log_loss": 2.64,
                    "uniform_log_loss": 2.91,
                    "position_brier": 0.917,
                    "uniform_brier": 0.946,
                    "mean_absolute_position_error": 3.31,
                    "uniform_mean_absolute_position_error": 4.61,
                    "rank_correlation": 0.65,
                    "mean_actual_position_probability": 0.094,
                },
                "folds": [],
                "acceptance": {"passed": True, "checks": {"position_log_loss": True}},
            }
        ),
        encoding="utf-8",
    )
    return forecast, backtest, position_backtest


def test_build_dashboard_payload_normalizes_artifacts(tmp_path: Path) -> None:
    forecast, backtest, position_backtest = _artifact_set(tmp_path)

    payload = build_dashboard_payload(forecast, backtest, position_backtest)

    assert payload["schema_version"] == 1
    assert payload["meta"]["season"] == "2026-27"
    assert payload["meta"]["simulations"] == 50_000
    assert payload["meta"]["source_alignment"]["matched_team_count"] == 2
    assert payload["freshness"]["source_status"] == "fresh"
    assert payload["freshness"]["source_notes"]
    assert [row["club"] for row in payload["championship"]] == [
        "Galatasaray SK",
        "Fenerbahçe SK",
    ]
    assert payload["championship"][0]["champion_probability"] == pytest.approx(0.6)
    assert payload["convergence"][0]["simulation_count"] == 10_000
    assert payload["fixtures"][0]["home_expected_goals"] == pytest.approx(1.6)
    assert payload["fixtures"][0]["predicted"] is True
    gala_first = next(
        row
        for row in payload["positions"]
        if row["club"] == "Galatasaray SK" and row["position"] == 1
    )
    assert gala_first == {
        "club": "Galatasaray SK",
        "position": 1,
        "count": 30_000,
        "probability": pytest.approx(0.6),
    }
    assert payload["expected_standings"][0]["expected_position"] == pytest.approx(1.4)
    assert payload["backtest"]["aggregate"]["hybrid_log_loss"] == pytest.approx(1.0017)
    assert payload["backtest"]["folds"][0]["season"] == 2025
    assert payload["position_backtest"]["aggregate"]["position_log_loss"] == pytest.approx(2.64)


def test_build_dashboard_payload_rejects_invalid_probability(tmp_path: Path) -> None:
    forecast, backtest, position_backtest = _artifact_set(tmp_path)
    championship = forecast / "champion-probabilities.csv"
    text = championship.read_text(encoding="utf-8").replace("0.6,0.004", "1.6,0.004")
    championship.write_text(text, encoding="utf-8")

    with pytest.raises(ValueError, match="champion_probability"):
        build_dashboard_payload(forecast, backtest, position_backtest)


def test_build_dashboard_payload_accepts_explicit_no_prediction(tmp_path: Path) -> None:
    forecast, backtest, position_backtest = _artifact_set(tmp_path)
    fixture = forecast / "fixture-expectations.csv"
    text = fixture.read_text(encoding="utf-8")
    text = text.replace(
        "away_win_probability\n",
        "away_win_probability,predicted\n",
    ).replace("0.3\n", "0.3,no\n")
    fixture.write_text(text, encoding="utf-8")

    payload = build_dashboard_payload(forecast, backtest, position_backtest)
    assert payload["fixtures"][0]["predicted"] is False
