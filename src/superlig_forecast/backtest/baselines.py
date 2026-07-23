"""Simple benchmark forecasts."""

import numpy as np
import numpy.typing as npt


def naive_one_x_two(n: int, frequencies: tuple[float, float, float]) -> npt.NDArray[np.float64]:
    return np.tile(np.asarray(frequencies, dtype=float), (n, 1))
