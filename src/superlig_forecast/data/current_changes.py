"""Immutable change detection for current squads and market values."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from datetime import date
from typing import Sequence

from superlig_forecast.data.identity import normalized_name


@dataclass(frozen=True, slots=True)
class PlayerObservation:
    provider_player_id: str | None
    player_name: str
    birth_date: str | None
    club: str
    market_value_eur: int | None
    observed_on: str
    observed: bool = True
    source_url: str | None = None

    def __post_init__(self) -> None:
        date.fromisoformat(self.observed_on)
        if self.market_value_eur is not None and self.market_value_eur < 0:
            raise ValueError("market value cannot be negative")


@dataclass(frozen=True, slots=True)
class TransferObservation:
    provider_player_id: str | None
    player_name: str
    from_club: str
    to_club: str
    observed_on: str


@dataclass(frozen=True, slots=True)
class ValuationChange:
    provider_player_id: str | None
    player_name: str
    club: str
    previous_value: int | None
    current_value: int | None
    observed_on: str


@dataclass(frozen=True, slots=True)
class SquadChangeSet:
    observations: tuple[PlayerObservation, ...]
    transfers: tuple[TransferObservation, ...]
    valuation_changes: tuple[ValuationChange, ...]
    unobserved: tuple[PlayerObservation, ...]


def _fallback_key(observation: PlayerObservation) -> tuple[str, str] | None:
    if observation.birth_date is None:
        return None
    return normalized_name(observation.player_name), observation.birth_date


def detect_current_changes(
    previous: Sequence[PlayerObservation],
    current: Sequence[PlayerObservation],
) -> SquadChangeSet:
    previous_by_id = {
        item.provider_player_id: (index, item)
        for index, item in enumerate(previous)
        if item.provider_player_id is not None
    }
    previous_keys = Counter(key for item in previous if (key := _fallback_key(item)) is not None)
    current_keys = Counter(key for item in current if (key := _fallback_key(item)) is not None)
    previous_by_key = {
        key: (index, item)
        for index, item in enumerate(previous)
        if (key := _fallback_key(item)) is not None
        and previous_keys[key] == 1
        and current_keys[key] == 1
    }

    matched_previous: set[int] = set()
    transfers: list[TransferObservation] = []
    valuation_changes: list[ValuationChange] = []
    for item in current:
        matched: tuple[int, PlayerObservation] | None = None
        if item.provider_player_id is not None:
            matched = previous_by_id.get(item.provider_player_id)
        if matched is None:
            key = _fallback_key(item)
            if key is not None and previous_keys[key] == 1 and current_keys[key] == 1:
                matched = previous_by_key.get(key)
        if matched is None:
            continue

        previous_index, old = matched
        matched_previous.add(previous_index)
        if normalized_name(old.club) != normalized_name(item.club):
            transfers.append(
                TransferObservation(
                    provider_player_id=item.provider_player_id or old.provider_player_id,
                    player_name=item.player_name,
                    from_club=old.club,
                    to_club=item.club,
                    observed_on=item.observed_on,
                )
            )
        if old.market_value_eur != item.market_value_eur:
            valuation_changes.append(
                ValuationChange(
                    provider_player_id=item.provider_player_id or old.provider_player_id,
                    player_name=item.player_name,
                    club=item.club,
                    previous_value=old.market_value_eur,
                    current_value=item.market_value_eur,
                    observed_on=item.observed_on,
                )
            )

    latest_observation = max(
        (item.observed_on for item in current),
        default=max((item.observed_on for item in previous), default="1970-01-01"),
    )
    unobserved = tuple(
        replace(item, observed_on=latest_observation, observed=False)
        for index, item in enumerate(previous)
        if index not in matched_previous
    )
    return SquadChangeSet(
        observations=tuple(previous) + tuple(current) + unobserved,
        transfers=tuple(transfers),
        valuation_changes=tuple(valuation_changes),
        unobserved=unobserved,
    )
