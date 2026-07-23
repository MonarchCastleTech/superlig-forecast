"""Immutable records shared across ingestion, modeling, and simulation."""

from datetime import datetime
from enum import StrEnum
from math import isclose
from typing import Annotated, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator


def _timezone_aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware")
    return value


AwareDateTime = Annotated[datetime, AfterValidator(_timezone_aware)]
Probability = Annotated[float, Field(ge=0.0, le=1.0)]
DecimalOdds = Annotated[float, Field(gt=1.0)]


class FrozenRecord(BaseModel):
    """Base class for immutable validated domain records."""

    model_config = ConfigDict(frozen=True)


class ForecastMode(StrEnum):
    """Information set used to create a forecast."""

    PRESEASON = "preseason"
    EXPECTED_LINEUP = "expected_lineup"
    CONFIRMED_LINEUP = "confirmed_lineup"
    LIVE_MATCHDAY = "live_matchday"


class MatchRecord(FrozenRecord):
    """A source-observed football match."""

    match_id: str
    competition_id: str
    season: str
    kickoff: AwareDateTime
    home_club_id: str
    away_club_id: str
    home_club_name: str
    away_club_name: str
    home_goals: int | None = Field(default=None, ge=0)
    away_goals: int | None = Field(default=None, ge=0)
    observed_at: AwareDateTime

    @property
    def is_finished(self) -> bool:
        """Whether a final score is present."""

        return self.home_goals is not None and self.away_goals is not None


class PlayerValuation(FrozenRecord):
    """A player's dated market valuation."""

    player_id: str
    club_id: str | None
    effective_date: AwareDateTime
    market_value_eur: int = Field(ge=0)
    observed_at: AwareDateTime


class OddsObservation(FrozenRecord):
    """Timestamped decimal 1X2 odds from one provider."""

    match_source_key: str
    provider: str
    observed_at: AwareDateTime
    home_odds: DecimalOdds
    draw_odds: DecimalOdds
    away_odds: DecimalOdds


class MatchForecast(FrozenRecord):
    """A coherent score and 1X2 probability forecast."""

    match_id: str
    mode: ForecastMode
    cutoff: AwareDateTime
    score_probabilities: tuple[tuple[Probability, ...], ...]
    home_probability: Probability
    draw_probability: Probability
    away_probability: Probability
    model_version: str
    data_hash: str
    quality_flags: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_probability_totals(self) -> Self:
        outcome_total = self.home_probability + self.draw_probability + self.away_probability
        score_total = sum(sum(row) for row in self.score_probabilities)
        if not isclose(outcome_total, 1.0, abs_tol=1e-9):
            raise ValueError("home, draw, and away probabilities must sum to 1")
        if not isclose(score_total, 1.0, abs_tol=1e-9):
            raise ValueError("score probabilities must sum to 1")
        return self

