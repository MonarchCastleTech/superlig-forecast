"""Static championship probability charts."""

from pathlib import Path

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
