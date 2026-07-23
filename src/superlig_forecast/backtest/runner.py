"""Backtest acceptance gates."""

from dataclasses import dataclass

from superlig_forecast.backtest.metrics import MetricComparison


@dataclass(frozen=True)
class GateResult:
    passed: bool
    failures: tuple[str, ...]


class AcceptanceGate:
    @staticmethod
    def evaluate(metrics: MetricComparison) -> GateResult:
        failures: list[str] = []
        if metrics.hybrid_log_loss >= metrics.best_non_market_log_loss:
            failures.append("log loss did not improve over the best non-market baseline")
        if metrics.hybrid_brier >= metrics.best_non_market_brier:
            failures.append("Brier score did not improve over the best non-market baseline")
        if (
            metrics.market_log_loss is not None
            and metrics.hybrid_log_loss > metrics.market_log_loss + 0.005
        ):
            failures.append("log loss exceeded the market-only tolerance")
        if (
            metrics.market_brier is not None
            and metrics.hybrid_brier > metrics.market_brier + 0.005
        ):
            failures.append("Brier score exceeded the market-only tolerance")
        return GateResult(not failures, tuple(failures))
