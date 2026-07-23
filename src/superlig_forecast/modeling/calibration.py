"""Probability calibration preserving score-matrix coherence."""

from typing import cast

import numpy as np
import numpy.typing as npt


def apply_temperature(
    matrix: npt.NDArray[np.float64], temperature: float
) -> npt.NDArray[np.float64]:
    if temperature <= 0:
        raise ValueError("temperature must be positive")
    logits = np.log(np.clip(matrix, 1e-15, 1.0)) / temperature
    calibrated = np.exp(logits - logits.max())
    return cast(npt.NDArray[np.float64], calibrated / calibrated.sum())
