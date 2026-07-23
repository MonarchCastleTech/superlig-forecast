from datetime import date

import numpy as np

from superlig_forecast.modeling.team_strength import (
    PlayedMatch,
    TeamStrengthModel,
    canonical_team_name,
)


def test_fitted_team_strength_rewards_repeated_goal_dominance() -> None:
    matches = [
        PlayedMatch(date(2024, 8, 1), 2024, "Alpha", "Beta", 3, 0),
        PlayedMatch(date(2024, 9, 1), 2024, "Beta", "Alpha", 0, 2),
        PlayedMatch(date(2024, 10, 1), 2024, "Alpha", "Beta", 2, 0),
        PlayedMatch(date(2024, 11, 1), 2024, "Beta", "Alpha", 1, 3),
    ]

    model = TeamStrengthModel.fit(matches, before_season=2025)
    alpha_home = model.predict_one_x_two("Alpha", "Beta")
    beta_home = model.predict_one_x_two("Beta", "Alpha")
    unseen = model.predict_one_x_two("New A", "New B")

    assert alpha_home[0] > beta_home[0]
    assert np.isclose(alpha_home.sum(), 1.0)
    assert np.isclose(unseen.sum(), 1.0)


def test_current_legal_names_resolve_to_historical_team_names() -> None:
    assert canonical_team_name("Fenerbahçe SK") == canonical_team_name("Fenerbahce")
    assert canonical_team_name("Beşiktaş JK") == canonical_team_name("Besiktas")
    assert canonical_team_name("Galatasaray A.Ş.") == canonical_team_name("Galatasaray")
    assert canonical_team_name("Corendon Alanyaspor") == canonical_team_name("Alanyaspor")
    assert canonical_team_name("Amed Sportif Faaliyetler") == canonical_team_name("Amed SK")
    assert canonical_team_name("Kasımpaşa") == canonical_team_name("Kasimpaşa A.Ş.")
