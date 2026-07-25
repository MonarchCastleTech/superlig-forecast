from superlig_forecast.modeling.structural import score_matrix
from superlig_forecast.simulation.rules import LeagueRules
from superlig_forecast.simulation.season import (
    FixtureForecast,
    SeasonSimulator,
    TeamStartingState,
)


def fixtures() -> list[FixtureForecast]:
    matrix = score_matrix(1.5, 1.1, -0.05)
    return [
        FixtureForecast(0, 1, matrix),
        FixtureForecast(2, 3, matrix),
        FixtureForecast(0, 2, matrix),
    ]


def test_same_seed_produces_identical_champion_counts() -> None:
    simulator = SeasonSimulator(("A", "B", "C", "D"), LeagueRules.default())
    first = simulator.simulate(fixtures(), n=10_000, seed=42)
    second = simulator.simulate(fixtures(), n=10_000, seed=42)
    assert first.champion_counts == second.champion_counts
    assert first.position_counts == second.position_counts


def test_total_points_match_draw_and_decisive_counts() -> None:
    result = SeasonSimulator(("A", "B", "C", "D"), LeagueRules.default()).simulate(
        fixtures(), n=2_000, seed=7
    )
    assert result.total_points == 2 * result.draw_count + 3 * result.decisive_count


def test_half_width_decreases_with_more_simulations() -> None:
    assert SeasonSimulator.half_width(5_000, 10_000) > SeasonSimulator.half_width(50_000, 100_000)


def test_checkpoint_simulation_records_prefix_sizes() -> None:
    simulator = SeasonSimulator(("A", "B", "C", "D"), LeagueRules.default())

    results = simulator.simulate_checkpoints(
        fixtures(), checkpoints=(100, 500), seed=9, chunk_size=100
    )

    assert list(results) == [100, 500]
    assert sum(results[500].champion_counts.values()) == 500


def test_simulation_aggregates_every_finishing_position() -> None:
    teams = ("A", "B", "C", "D")
    result = SeasonSimulator(teams, LeagueRules.default()).simulate(
        fixtures(), n=2_000, seed=11, chunk_size=250
    )

    assert set(result.position_counts) == set(teams)
    assert all(len(counts) == len(teams) for counts in result.position_counts.values())
    assert all(sum(counts) == 2_000 for counts in result.position_counts.values())
    assert [
        sum(result.position_counts[team][position] for team in teams)
        for position in range(len(teams))
    ] == [2_000] * len(teams)
    assert {
        team: counts[0] for team, counts in result.position_counts.items()
    } == result.champion_counts


def test_simulation_records_team_point_and_goal_difference_sums() -> None:
    teams = ("A", "B", "C", "D")
    result = SeasonSimulator(teams, LeagueRules.default()).simulate(fixtures(), n=500, seed=5)

    assert set(result.point_sums) == set(teams)
    assert set(result.goal_difference_sums) == set(teams)
    assert sum(result.point_sums.values()) == result.total_points
    assert sum(result.goal_difference_sums.values()) == 0


def test_simulation_starts_from_completed_match_table_state() -> None:
    teams = ("A", "B")
    initial = (
        TeamStartingState(points=3, goals_for=2, goals_against=0),
        TeamStartingState(points=0, goals_for=0, goals_against=2),
    )
    simulator = SeasonSimulator(teams, LeagueRules.default(), initial=initial)

    result = simulator.simulate([], n=100, seed=3)

    assert result.champion_counts == {"A": 100, "B": 0}
    assert result.point_sums == {"A": 300, "B": 0}
    assert result.goal_difference_sums == {"A": 200, "B": -200}
