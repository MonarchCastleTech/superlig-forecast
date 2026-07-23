"""Expected-lineup calculations."""


def expected_start_probabilities(selection_weights: list[float]) -> list[float]:
    if len(selection_weights) < 11:
        raise ValueError("at least eleven eligible players are required")
    weights = [max(0.0, float(value)) for value in selection_weights]
    if sum(weights) == 0:
        return [11.0 / len(weights)] * len(weights)
    low, high = 0.0, 11.0 / min(value for value in weights if value > 0)
    for _ in range(80):
        scale = (low + high) / 2
        total = sum(min(1.0, scale * value) for value in weights)
        if total < 11:
            low = scale
        else:
            high = scale
    return [min(1.0, high * value) for value in weights]
