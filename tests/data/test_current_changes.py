from superlig_forecast.data.current_changes import (
    PlayerObservation,
    detect_current_changes,
)


def player(
    player_id: str | None,
    club: str,
    value: int | None,
    observed_on: str,
    *,
    name: str = "Player One",
    birth_date: str | None = "2000-01-01",
) -> PlayerObservation:
    return PlayerObservation(
        provider_player_id=player_id,
        player_name=name,
        birth_date=birth_date,
        club=club,
        market_value_eur=value,
        observed_on=observed_on,
    )


def test_detects_transfer_and_value_change_without_overwriting_history() -> None:
    previous = [player("p1", "Club A", 1_000_000, "2026-07-01")]
    current = [player("p1", "Club B", 1_500_000, "2026-07-25")]
    changes = detect_current_changes(previous, current)
    assert changes.transfers[0].from_club == "Club A"
    assert changes.transfers[0].to_club == "Club B"
    assert changes.valuation_changes[0].previous_value == 1_000_000
    assert len(changes.observations) == 2


def test_uses_unique_name_birth_fallback_and_marks_missing_unobserved() -> None:
    previous = [
        player(None, "Club A", 500_000, "2026-07-01"),
        player("p2", "Club A", 750_000, "2026-07-01", name="Missing"),
    ]
    current = [
        player(
            None,
            "Club B",
            500_000,
            "2026-07-25",
        )
    ]
    changes = detect_current_changes(previous, current)
    assert changes.transfers[0].player_name == "Player One"
    missing = [
        item for item in changes.observations if item.player_name == "Missing" and not item.observed
    ]
    assert len(missing) == 1
