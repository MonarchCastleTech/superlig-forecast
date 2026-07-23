"""Static championship probability charts."""

from pathlib import Path
from typing import cast

import matplotlib.pyplot as plt
import polars as pl


def championship_timeline(frame: pl.DataFrame, output: Path) -> Path:
    figure, axis = plt.subplots(figsize=(12, 7))
    for club in frame["club_id"].unique().sort().to_list():
        rows = frame.filter(pl.col("club_id") == club).sort("observed_at")
        axis.plot(rows["observed_at"], rows["champion_probability"], label=club)
    axis.set_ylabel("Championship probability")
    axis.set_ylim(0, 1)
    axis.legend()
    figure.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=150)
    plt.close(figure)
    return output


def championship_convergence(frame: pl.DataFrame, output: Path) -> Path:
    """Plot cumulative Monte Carlo title probabilities against sample size."""

    figure, (axis, detail_axis) = plt.subplots(1, 2, figsize=(17, 7))
    final_count = frame["simulation_count"].max()
    final = frame.filter(pl.col("simulation_count") == final_count).sort(
        "champion_probability", descending=True
    )
    ordered = final["club_id"].to_list()
    for club in ordered[:6]:
        rows = frame.filter(pl.col("club_id") == club).sort("simulation_count")
        axis.plot(
            rows["simulation_count"],
            rows["champion_probability"],
            marker="o",
            linewidth=1.6,
            label=club,
        )
    for club in ordered:
        rows = frame.filter(pl.col("club_id") == club).sort("simulation_count")
        detail_axis.plot(
            rows["simulation_count"],
            rows["champion_probability"],
            marker="o",
            linewidth=1.2,
            label=club,
        )
    axis.set_xscale("log")
    axis.set_xlabel("Monte Carlo simulations")
    axis.set_ylabel("Championship probability")
    axis.set_title("Leading contenders")
    maximum_probability = cast(float, final["champion_probability"].max())
    axis.set_ylim(0, max(0.05, maximum_probability * 1.12))
    axis.grid(alpha=0.2)
    axis.legend(fontsize=8)
    detail_axis.set_xscale("log")
    detail_axis.set_yscale("log")
    detail_axis.set_xlabel("Monte Carlo simulations")
    detail_axis.set_ylabel("Championship probability (log scale)")
    detail_axis.set_title("Long-tail detail")
    detail_axis.grid(alpha=0.2)
    detail_axis.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    figure.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=160)
    plt.close(figure)
    return output


def backtest_log_loss_chart(frame: pl.DataFrame, output: Path) -> Path:
    """Plot proper-score movement across walk-forward test seasons."""

    figure, axis = plt.subplots(figsize=(12, 7))
    for column, label in (
        ("naive_log_loss", "Naive"),
        ("structural_log_loss", "Structural"),
        ("hybrid_log_loss", "Hybrid"),
        ("market_log_loss", "Market-only"),
    ):
        axis.plot(frame["season"], frame[column], marker="o", label=label)
    axis.set_xlabel("Season start year")
    axis.set_ylabel("Multiclass log loss (lower is better)")
    axis.grid(alpha=0.2)
    axis.legend()
    figure.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=160)
    plt.close(figure)
    return output
