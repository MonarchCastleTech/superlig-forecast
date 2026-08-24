"""Assemble a current-season Monte Carlo model from history and squad values."""

from dataclasses import dataclass
from typing import Any, Mapping

from superlig_forecast.data.identity import normalized_name
from superlig_forecast.data.structured_sources import StructuredMatch
from superlig_forecast.data.transfermarkt_live import CurrentSquadValue
from superlig_forecast.modeling.hybrid import one_x_two_from_matrix
from superlig_forecast.modeling.squad_value import adjust_expected_goals_for_value
from superlig_forecast.modeling.structural import score_matrix
from superlig_forecast.modeling.team_strength import (
    PlayedMatch,
    TeamRates,
    TeamStrengthModel,
)
from superlig_forecast.simulation.season import FixtureForecast, TeamStartingState


@dataclass(frozen=True)
class FixtureExpectation:
    home_team: str
    away_team: str
    home_expected_goals: float
    away_expected_goals: float
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    # Presentation metadata only. It never enters the model or probabilities.
    predicted: bool = True


@dataclass(frozen=True)
class PreparedCurrentSeason:
    team_ids: tuple[str, ...]
    fixtures: list[FixtureForecast]
    expectations: tuple[FixtureExpectation, ...]
    squad_values: dict[str, int]
    starting_table: dict[str, TeamStartingState]


def model_from_artifact(payload: Mapping[str, Any]) -> TeamStrengthModel:
    """Restore the compact trained model used by stateless update runners."""

    raw_rates = payload.get("team_rates")
    if not isinstance(raw_rates, Mapping):
        raise ValueError("model artifact team_rates must be an object")
    rates: dict[str, TeamRates] = {}
    for team, raw in raw_rates.items():
        if not isinstance(team, str) or not isinstance(raw, Mapping):
            raise ValueError("model artifact contains an invalid team rate")
        rates[team] = TeamRates(
            float(raw["home_attack"]),
            float(raw["home_defence"]),
            float(raw["away_attack"]),
            float(raw["away_defence"]),
        )
    return TeamStrengthModel(
        float(payload["league_home_goals"]),
        float(payload["league_away_goals"]),
        rates,
        float(payload.get("rho", -0.05)),
    )


def _match_key(value: str) -> str:
    tokens = normalized_name(value).split()
    while len(tokens) > 1 and tokens[-1] in {"a", "s", "as", "sk", "fk"}:
        tokens.pop()
    return "".join(tokens)


def prepare_current_season_from_model(
    model: TeamStrengthModel,
    squads: list[CurrentSquadValue],
    *,
    played_matches: list[StructuredMatch] | None = None,
    value_coefficient: float = 0.1,
) -> PreparedCurrentSeason:
    """Build remaining fixtures and the table state from completed matches."""

    team_ids = tuple(sorted(item.club_name for item in squads))
    values = {item.club_name: item.squad_value_eur for item in squads}
    if len(values) != len(squads):
        raise ValueError("current squad list contains duplicate club names")
    team_by_key = {_match_key(team): team for team in team_ids}
    completed: dict[tuple[str, str], tuple[int, int]] = {}
    starting_table = {team: TeamStartingState() for team in team_ids}
    for match in played_matches or []:
        if match.status != "finished":
            continue
        home = team_by_key.get(_match_key(match.home_team))
        away = team_by_key.get(_match_key(match.away_team))
        if home is None or away is None or match.home_score is None or match.away_score is None:
            continue
        completed[(home, away)] = (match.home_score, match.away_score)
        home_row = starting_table[home]
        away_row = starting_table[away]
        home_points = (
            3 if match.home_score > match.away_score else int(match.home_score == match.away_score)
        )
        away_points = (
            3 if match.away_score > match.home_score else int(match.home_score == match.away_score)
        )
        starting_table[home] = TeamStartingState(
            home_row.points + home_points,
            home_row.goals_for + match.home_score,
            home_row.goals_against + match.away_score,
        )
        starting_table[away] = TeamStartingState(
            away_row.points + away_points,
            away_row.goals_for + match.away_score,
            away_row.goals_against + match.home_score,
        )

    fixtures: list[FixtureForecast] = []
    expectations: list[FixtureExpectation] = []
    for home_index, home_team in enumerate(team_ids):
        for away_index, away_team in enumerate(team_ids):
            if home_index == away_index:
                continue
            if (home_team, away_team) in completed:
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
        starting_table,
    )


def prepare_current_season(
    history: list[PlayedMatch],
    squads: list[CurrentSquadValue],
    *,
    season: int,
    value_coefficient: float = 0.1,
) -> PreparedCurrentSeason:
    """Fit from history and build every ordered current-season fixture."""

    return prepare_current_season_from_model(
        TeamStrengthModel.fit(history, before_season=season),
        squads,
        value_coefficient=value_coefficient,
    )
