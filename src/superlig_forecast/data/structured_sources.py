"""Normalized records and strict reconciliation for structured football feeds."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal, Sequence

from superlig_forecast.data.identity import normalized_name

MatchStatus = Literal["scheduled", "finished", "postponed", "cancelled"]


class ReconciliationError(RuntimeError):
    """Raised when two authoritative feeds cannot be safely reconciled."""


def _canonical_club(value: str) -> str:
    tokens = normalized_name(value).split()
    removable_suffixes = {"a", "s", "as", "sk", "fk"}
    while len(tokens) > 1 and tokens[-1] in removable_suffixes:
        tokens.pop()
    return " ".join(tokens)


@dataclass(frozen=True, slots=True)
class StructuredMatch:
    played_on: str
    home_team: str
    away_team: str
    home_score: int | None
    away_score: int | None
    status: MatchStatus
    provider_id: str | None = None

    def __post_init__(self) -> None:
        date.fromisoformat(self.played_on)
        if (self.home_score is None) != (self.away_score is None):
            raise ValueError("match scores must both be present or both be absent")
        if self.status == "finished" and self.home_score is None:
            raise ValueError("finished matches require a score")
        if self.home_score is not None and (
            self.home_score < 0 or self.away_score is None or self.away_score < 0
        ):
            raise ValueError("match scores cannot be negative")


@dataclass(frozen=True, slots=True)
class ProviderBatch:
    provider: str
    competition: str
    season: str
    fetched_at: str
    matches: tuple[StructuredMatch, ...]
    expected_clubs: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        provider_ids = [
            match.provider_id
            for match in self.matches
            if match.provider_id is not None
        ]
        if len(provider_ids) != len(set(provider_ids)):
            raise ValueError("duplicate provider id")

        fixture_keys = [
            (
                match.played_on,
                _canonical_club(match.home_team),
                _canonical_club(match.away_team),
            )
            for match in self.matches
        ]
        if len(fixture_keys) != len(set(fixture_keys)):
            raise ValueError("duplicate home/away/date fixture")

        if self.expected_clubs:
            observed = {
                _canonical_club(team)
                for match in self.matches
                for team in (match.home_team, match.away_team)
            }
            expected = {_canonical_club(team) for team in self.expected_clubs}
            if observed != expected:
                missing = sorted(expected - observed)
                extra = sorted(observed - expected)
                raise ValueError(
                    f"club coverage mismatch: missing={missing}, extra={extra}"
                )


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    matched: int
    only_primary: tuple[StructuredMatch, ...]
    only_verification: tuple[StructuredMatch, ...]
    conflicts: tuple[str, ...]


def _matches(
    primary: StructuredMatch,
    verification: StructuredMatch,
) -> bool:
    if _canonical_club(primary.home_team) != _canonical_club(
        verification.home_team
    ):
        return False
    if _canonical_club(primary.away_team) != _canonical_club(
        verification.away_team
    ):
        return False
    primary_date = date.fromisoformat(primary.played_on)
    verification_date = date.fromisoformat(verification.played_on)
    return abs((primary_date - verification_date).days) <= 1


def _unpack(
    source: ProviderBatch | Sequence[StructuredMatch],
) -> tuple[str | None, tuple[StructuredMatch, ...]]:
    if isinstance(source, ProviderBatch):
        return source.competition, source.matches
    return None, tuple(source)


def reconcile_matches(
    primary: ProviderBatch | Sequence[StructuredMatch],
    verification: ProviderBatch | Sequence[StructuredMatch],
) -> ReconciliationReport:
    primary_competition, primary_matches = _unpack(primary)
    verification_competition, verification_matches = _unpack(verification)
    if (
        primary_competition is not None
        and verification_competition is not None
        and normalized_name(primary_competition)
        != normalized_name(verification_competition)
    ):
        raise ReconciliationError("competition conflict")

    used_verification: set[int] = set()
    only_primary: list[StructuredMatch] = []
    conflicts: list[str] = []
    matched = 0

    for primary_match in primary_matches:
        candidates = [
            (index, candidate)
            for index, candidate in enumerate(verification_matches)
            if index not in used_verification
            and _matches(primary_match, candidate)
        ]
        if not candidates:
            only_primary.append(primary_match)
            continue
        candidates.sort(
            key=lambda item: abs(
                (
                    date.fromisoformat(primary_match.played_on)
                    - date.fromisoformat(item[1].played_on)
                ).days
            )
        )
        index, verification_match = candidates[0]
        used_verification.add(index)
        matched += 1

        if primary_match.status != verification_match.status:
            conflicts.append(
                "status conflict for "
                f"{primary_match.home_team} vs {primary_match.away_team}: "
                f"{primary_match.status} != {verification_match.status}"
            )
        if (
            primary_match.status == "finished"
            and verification_match.status == "finished"
            and (
                primary_match.home_score != verification_match.home_score
                or primary_match.away_score != verification_match.away_score
            )
        ):
            raise ReconciliationError(
                "score conflict for "
                f"{primary_match.home_team} vs {primary_match.away_team}"
            )

    only_verification = tuple(
        match
        for index, match in enumerate(verification_matches)
        if index not in used_verification
    )
    return ReconciliationReport(
        matched=matched,
        only_primary=tuple(only_primary),
        only_verification=only_verification,
        conflicts=tuple(conflicts),
    )
