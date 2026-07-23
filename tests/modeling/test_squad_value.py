from superlig_forecast.modeling.squad_value import adjust_expected_goals_for_value


def test_more_valuable_squad_shifts_expected_goals_toward_it() -> None:
    home, away = adjust_expected_goals_for_value(
        1.5,
        1.2,
        home_value_eur=300_000_000,
        away_value_eur=30_000_000,
        coefficient=0.1,
    )

    assert home > 1.5
    assert away < 1.2
