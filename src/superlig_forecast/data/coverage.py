"""Feature coverage and model-mode eligibility."""

from pydantic import BaseModel, ConfigDict


class MarketEligibility(BaseModel):
    model_config = ConfigDict(frozen=True)

    coverage: float
    eligible: bool


def market_eligibility(total_matches: int, matches_with_cutoff_odds: int) -> MarketEligibility:
    if total_matches <= 0:
        raise ValueError("total_matches must be positive")
    if not 0 <= matches_with_cutoff_odds <= total_matches:
        raise ValueError("matches_with_cutoff_odds must be within total matches")
    coverage = matches_with_cutoff_odds / total_matches
    return MarketEligibility(coverage=coverage, eligible=coverage >= 0.80)

