"""Assemble a current-season Monte Carlo model from history and squad values."""

from dataclasses import dataclass

from superlig_forecast.data.transfermarkt_live import CurrentSquadValue
from superlig_forecast.modeling.hybrid import one_x_two_from_matrix
from superlig_forecast.modeling.squad_value import adjust_expected_goals_for_value
from superlig_forecast.modeling.structural import score_matrix
from superlig_forecast.modeling.team_strength import PlayedMatch, TeamStrengthModel
from superlig_forecast.simulation.season import FixtureForecast


@dataclass(frozen=True)
class FixtureExpectation:
    home_team: str
    away_team: str
    home_expected_goals: float
    away_expected_goals: float
    home_win_probability: float
    draw_probability: float
    away_win_probability: float


@dataclass(frozen=True)
class PreparedCurrentSeason:
    team_ids: tuple[str, ...]
    fixtures: list[FixtureForecast]
    expectations: tuple[FixtureExpectation, ...]
    squad_values: dict[str, int]


def prepare_current_season(
    history: list[PlayedMatch],
    squads: list[CurrentSquadValue],
    *,
    season: int,
    value_coefficient: float = 0.1,
) -> PreparedCurrentSeason:
    """Build every ordered home/away fixture with current value adjustments."""

    team_ids = tuple(sorted(item.club_name for item in squads))
    values = {item.club_name: item.squad_value_eur for item in squads}
    if len(values) != len(squads):
        raise ValueError("current squad list contains duplicate club names")
    model = TeamStrengthModel.fit(history, before_season=season)
    fixtures: list[FixtureForecast] = []
    expectations: list[FixtureExpectation] = []
    for home_index, home_team in enumerate(team_ids):
        for away_index, away_team in enumerate(team_ids):
            if home_index == away_index:
                continue
            home_goals, away_goals = model.expected_goals(home_team, away_team)
            home_goals, away_goals = adjust_expected_goals_for_value(
                home_goals,
                away_goals,
                home_value_eur=values[home_team],
                away_value_eur=values[away_team],
                coefficient=value_coefficient,
            )
            matrix = score_matrix(home_goals, away_goals, model.rho)
            probabilities = one_x_two_from_matrix(matrix)
            fixtures.append(FixtureForecast(home_index, away_index, matrix))
            expectations.append(
                FixtureExpectation(
                    home_team,
                    away_team,
                    home_goals,
                    away_goals,
                    float(probabilities[0]),
                    float(probabilities[1]),
                    float(probabilities[2]),
                )
            )
    return PreparedCurrentSeason(
        team_ids,
        fixtures,
        tuple(expectations),
        values,
    )
