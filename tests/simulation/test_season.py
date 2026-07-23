from superlig_forecast.modeling.structural import score_matrix
from superlig_forecast.simulation.rules import LeagueRules
from superlig_forecast.simulation.season import FixtureForecast, SeasonSimulator


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
