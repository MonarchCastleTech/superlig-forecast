from datetime import date

from superlig_forecast.data.identity import ClubAlias, IdentityResolver


def test_cross_source_aliases_resolve_to_stable_id() -> None:
    resolver = IdentityResolver(
        [
            ClubAlias("tff", "55", "İstanbul Başakşehir FK", "club:basaksehir"),
            ClubAlias("tm", "6890", "Başakşehir", "club:basaksehir"),
        ]
    )

    first = resolver.resolve_club("tff", "55", "İstanbul Başakşehir FK", date(2015, 1, 1))
    second = resolver.resolve_club("tm", "6890", "Başakşehir", date(2025, 1, 1))

    assert first == second == "club:basaksehir"
