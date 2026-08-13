"""Recency-weighted, promoted-team-safe structural goal model."""

from dataclasses import dataclass
from datetime import date
import unicodedata

import numpy as np
import numpy.typing as npt

from superlig_forecast.modeling.hybrid import one_x_two_from_matrix
from superlig_forecast.modeling.structural import score_matrix


def canonical_team_name(value: str) -> str:
    """Normalize common source spelling differences without fuzzy matching."""

    value = value.replace("ı", "i").replace("İ", "I")
    folded = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    normalized = "".join(character for character in folded.lower() if character.isalnum())
    aliases = {
        "istanbulbuyuksehirbelediyespor": "istanbulbasaksehir",
        "buyuksehyr": "istanbulbasaksehir",
        "istanbulbasaksehirfk": "istanbulbasaksehir",
        "basaksehirfk": "istanbulbasaksehir",
        "fenerbahcesk": "fenerbahce",
        "fenerbahceas": "fenerbahce",
        "galatasaraysk": "galatasaray",
        "galatasarayas": "galatasaray",
        "besiktasjk": "besiktas",
        "besiktasas": "besiktas",
        "besiktasjimnastikkulubu": "besiktas",
        "corendonalanyaspor": "alanyaspor",
        "amedsk": "amed",
        "amedsportiffaaliyetler": "amed",
        "kasimpasaas": "kasimpasa",
        "goztepeas": "goztepe",
        "samsunsporas": "samsunspor",
        "trabzonsporas": "trabzonspor",
        "caykurrizesporas": "caykurrizespor",
        "genclerbirligisk": "genclerbirligi",
        "genclerbirligiankara": "genclerbirligi",
        "genclerbirligisporkulubu": "genclerbirligi",
        "gaziantepbb": "gaziantepfk",
        "gaziantepfutbolkulubuas": "gaziantepfk",
        "erzurumbb": "erzurumspor",
        "erzurumsporfk": "erzurumspor",
        "arcacorumfk": "corumfk",
        "tumosankonyaspor": "konyaspor",
    }
    return aliases.get(normalized, normalized)


@dataclass(frozen=True)
class PlayedMatch:
    date: date
    season: int
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int


@dataclass(frozen=True)
class TeamRates:
    home_attack: float
    home_defence: float
    away_attack: float
    away_defence: float


@dataclass(frozen=True)
class TeamStrengthModel:
    league_home_goals: float
    league_away_goals: float
    rates: dict[str, TeamRates]
    rho: float = -0.05

    @classmethod
    def fit(
        cls,
        matches: list[PlayedMatch],
        *,
        before_season: int,
        decay: float = 0.68,
        seasons: int = 5,
        prior_matches: float = 6.0,
    ) -> "TeamStrengthModel":
        eligible = [
            match for match in matches if before_season - seasons <= match.season < before_season
        ]
        weighted: dict[str, list[float]] = {}
        league_home_goals = league_away_goals = league_matches = 0.0
        for match in eligible:
            weight = decay ** max(0, before_season - 1 - match.season)
            league_home_goals += weight * match.home_goals
            league_away_goals += weight * match.away_goals
            league_matches += weight
            home = weighted.setdefault(canonical_team_name(match.home_team), [0.0] * 6)
            away = weighted.setdefault(canonical_team_name(match.away_team), [0.0] * 6)
            home[0] += weight * match.home_goals
            home[1] += weight * match.away_goals
            home[2] += weight
            away[3] += weight * match.away_goals
            away[4] += weight * match.home_goals
            away[5] += weight
        home_average = league_home_goals / league_matches if league_matches else 1.45
        away_average = league_away_goals / league_matches if league_matches else 1.15
        rates: dict[str, TeamRates] = {}
        for team, values in weighted.items():
            home_scored, home_allowed, home_n, away_scored, away_allowed, away_n = values
            home_rate = (home_scored + prior_matches * home_average) / (home_n + prior_matches)
            home_concede = (home_allowed + prior_matches * away_average) / (home_n + prior_matches)
            away_rate = (away_scored + prior_matches * away_average) / (away_n + prior_matches)
            away_concede = (away_allowed + prior_matches * home_average) / (away_n + prior_matches)
            rates[team] = TeamRates(
                home_attack=home_rate / home_average,
                home_defence=home_concede / away_average,
                away_attack=away_rate / away_average,
                away_defence=away_concede / home_average,
            )
        return cls(home_average, away_average, rates)

    def expected_goals(self, home_team: str, away_team: str) -> tuple[float, float]:
        neutral = TeamRates(1.0, 1.0, 1.0, 1.0)
        home = self.rates.get(canonical_team_name(home_team), neutral)
        away = self.rates.get(canonical_team_name(away_team), neutral)
        home_goals = float(
            np.clip(self.league_home_goals * home.home_attack * away.away_defence, 0.2, 4.5)
        )
        away_goals = float(
            np.clip(self.league_away_goals * away.away_attack * home.home_defence, 0.2, 4.5)
        )
        return home_goals, away_goals

    def predict_score_matrix(self, home_team: str, away_team: str) -> npt.NDArray[np.float64]:
        home_goals, away_goals = self.expected_goals(home_team, away_team)
        return score_matrix(home_goals, away_goals, self.rho)

    def predict_one_x_two(self, home_team: str, away_team: str) -> npt.NDArray[np.float64]:
        return one_x_two_from_matrix(self.predict_score_matrix(home_team, away_team))
