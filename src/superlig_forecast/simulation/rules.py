"""Versioned league-table rules."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LeagueRules:
    win_points: int
    draw_points: int
    loss_points: int
    tie_breakers: tuple[str, ...]

    @classmethod
    def default(cls) -> "LeagueRules":
        return cls(3, 1, 0, ("points", "head_to_head", "goal_difference", "goals_for"))

