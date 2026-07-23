"""Season- and position-relative market-value features."""

import polars as pl


def normalize_market_values(frame: pl.DataFrame) -> pl.DataFrame:
    groups = ["season", "position"]
    return frame.with_columns(pl.col("market_value_eur").log1p().alias("_log_value")).with_columns(
        (
            (pl.col("_log_value") - pl.col("_log_value").median().over(groups))
            / (
                pl.col("_log_value").quantile(0.75).over(groups)
                - pl.col("_log_value").quantile(0.25).over(groups)
            ).clip(lower_bound=0.1)
        ).alias("value_score")
    ).drop("_log_value")
