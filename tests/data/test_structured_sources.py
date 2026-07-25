import pytest

from superlig_forecast.data.structured_sources import (
    ProviderBatch,
    ReconciliationError,
    StructuredMatch,
    reconcile_matches,
)


def test_reconcile_matches_accepts_equivalent_normalized_fixture() -> None:
    api = StructuredMatch(
        "2026-08-14",
        "Galatasaray",
        "Fenerbahçe",
        2,
        1,
        "finished",
    )
    tff = StructuredMatch(
        "2026-08-14",
        "GALATASARAY A.Ş.",
        "FENERBAHÇE A.Ş.",
        2,
        1,
        "finished",
    )
    report = reconcile_matches([api], [tff])
    assert report.matched == 1
    assert report.conflicts == ()


def test_reconcile_matches_rejects_score_conflict() -> None:
    api = StructuredMatch("2026-08-14", "A", "B", 2, 1, "finished")
    tff = StructuredMatch("2026-08-14", "A", "B", 1, 1, "finished")
    with pytest.raises(ReconciliationError, match="score conflict"):
        reconcile_matches([api], [tff])


def test_provider_batch_rejects_duplicate_ids_and_incomplete_club_set() -> None:
    match = StructuredMatch(
        "2026-08-14",
        "A",
        "B",
        None,
        None,
        "scheduled",
        provider_id="fixture-1",
    )
    with pytest.raises(ValueError, match="duplicate provider id"):
        ProviderBatch(
            provider="api",
            competition="TSL",
            season="2026-27",
            fetched_at="2026-07-25T12:00:00Z",
            matches=(match, match),
        )
    with pytest.raises(ValueError, match="club coverage mismatch"):
        ProviderBatch(
            provider="api",
            competition="TSL",
            season="2026-27",
            fetched_at="2026-07-25T12:00:00Z",
            matches=(match,),
            expected_clubs=frozenset({"A", "B", "C"}),
        )
