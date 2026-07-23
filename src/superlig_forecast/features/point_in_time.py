"""Point-in-time joins."""

import polars as pl


def asof_join(
    left: pl.DataFrame,
    right: pl.DataFrame,
    *,
    by: list[str],
    left_time: str,
    right_time: str,
) -> pl.DataFrame:
    return left.sort([*by, left_time]).join_asof(
        right.sort([*by, right_time]),
        left_on=left_time,
        right_on=right_time,
        by=by,
        strategy="backward",
        check_sortedness=False,
    )
