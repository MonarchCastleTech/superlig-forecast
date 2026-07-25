import { describe, expect, it } from "vitest";

import {
  filterFixtures,
  formatProbability,
  leaderAtPosition,
  positionDistribution,
  rankAtCheckpoint,
  validateDashboardPayload,
  type DashboardPayload,
} from "./dashboard-data";

const payload: DashboardPayload = {
  schema_version: 1,
  meta: {
    season: "2026-27",
    simulations: 50_000,
    seed: 202627,
    model_version: "0.1.0",
    team_count: 2,
    fixture_count: 2,
    checkpoints: [10_000, 50_000],
    value_coefficient: 0.1,
    source_alignment: null,
  },
  freshness: {
    generated_at: "2026-07-25T12:00:00Z",
    match_snapshot_at: "2026-07-25T11:00:00Z",
    squad_snapshot_at: "2026-07-24T12:00:00Z",
    valuation_snapshot_at: "2026-07-24T12:00:00Z",
    latest_match_date: null,
    source_status: "fresh",
    source_notes: [],
  },
  championship: [
    {
      club: "Galatasaray SK",
      squad_value_eur: 323_300_000,
      champion_count: 30_000,
      champion_probability: 0.6,
      ci95_half_width: 0.004,
    },
    {
      club: "Fenerbahçe SK",
      squad_value_eur: 333_150_000,
      champion_count: 20_000,
      champion_probability: 0.4,
      ci95_half_width: 0.004,
    },
  ],
  convergence: [
    {
      simulation_count: 10_000,
      club: "Galatasaray SK",
      champion_probability: 0.45,
    },
    {
      simulation_count: 10_000,
      club: "Fenerbahçe SK",
      champion_probability: 0.55,
    },
    {
      simulation_count: 50_000,
      club: "Galatasaray SK",
      champion_probability: 0.6,
    },
    {
      simulation_count: 50_000,
      club: "Fenerbahçe SK",
      champion_probability: 0.4,
    },
  ],
  fixtures: [
    {
      home_team: "Galatasaray SK",
      away_team: "Fenerbahçe SK",
      home_expected_goals: 1.7,
      away_expected_goals: 1.2,
      home_win_probability: 0.51,
      draw_probability: 0.25,
      away_win_probability: 0.24,
    },
    {
      home_team: "Fenerbahçe SK",
      away_team: "Galatasaray SK",
      home_expected_goals: 1.4,
      away_expected_goals: 1.3,
      home_win_probability: 0.35,
      draw_probability: 0.28,
      away_win_probability: 0.37,
    },
  ],
  positions: [
    { club: "Galatasaray SK", position: 1, count: 30_000, probability: 0.6 },
    { club: "Galatasaray SK", position: 2, count: 20_000, probability: 0.4 },
    { club: "Fenerbahçe SK", position: 1, count: 20_000, probability: 0.4 },
    { club: "Fenerbahçe SK", position: 2, count: 30_000, probability: 0.6 },
  ],
  expected_standings: [
    {
      club: "Galatasaray SK",
      expected_position: 1.4,
      median_position: 1,
      most_likely_position: 1,
      expected_points: 78.2,
      expected_goal_difference: 42.1,
      top_four_probability: 1,
      position_17_probability: null,
      relegation_probability: 0,
    },
    {
      club: "Fenerbahçe SK",
      expected_position: 1.6,
      median_position: 2,
      most_likely_position: 2,
      expected_points: 76.4,
      expected_goal_difference: 39.7,
      top_four_probability: 1,
      position_17_probability: null,
      relegation_probability: 0,
    },
  ],
  backtest: {
    method: "strict-expanding-window",
    start_season: 2006,
    end_season: 2025,
    market_weight: 0.9,
    fold_count: 20,
    match_count: 6437,
    market_match_count: 4074,
    aggregate: {
      naive_log_loss: 1.0655,
      hybrid_log_loss: 1.0017,
    },
    folds: [],
    acceptance: { passed: true, checks: {} },
  },
  position_backtest: {
    method: "strict-preseason-expanding-window-position-distribution",
    start_season: 2006,
    end_season: 2025,
    fold_count: 20,
    simulations_per_fold: 20_000,
    aggregate: {
      position_log_loss: 2.64,
      uniform_log_loss: 2.91,
      position_brier: 0.917,
      uniform_brier: 0.946,
      mean_absolute_position_error: 3.31,
      uniform_mean_absolute_position_error: 4.61,
      rank_correlation: 0.65,
      mean_actual_position_probability: 0.094,
    },
    folds: [],
    acceptance: { passed: true, checks: {} },
  },
};

describe("dashboard data selectors", () => {
  it("ranks clubs at the selected checkpoint", () => {
    expect(rankAtCheckpoint(payload, 10_000).map((team) => team.club)).toEqual([
      "Fenerbahçe SK",
      "Galatasaray SK",
    ]);
    expect(rankAtCheckpoint(payload, 50_000)[0]).toMatchObject({
      club: "Galatasaray SK",
      champion_probability: 0.6,
    });
  });

  it("filters fixtures by club and strongest outcome", () => {
    expect(filterFixtures(payload.fixtures, "galata", "home")).toHaveLength(1);
    expect(filterFixtures(payload.fixtures, "FENER", "away")).toHaveLength(1);
    expect(filterFixtures(payload.fixtures, "", "draw")).toHaveLength(0);
  });

  it("formats unit probabilities and missing values", () => {
    expect(formatProbability(0.5514416, 2)).toBe("55.14%");
    expect(formatProbability(null)).toBe("Not available");
  });

  it("returns a club distribution and exact-position leader", () => {
    expect(positionDistribution(payload, "Fenerbahçe SK")).toEqual([
      { club: "Fenerbahçe SK", position: 1, count: 20_000, probability: 0.4 },
      { club: "Fenerbahçe SK", position: 2, count: 30_000, probability: 0.6 },
    ]);
    expect(leaderAtPosition(payload, 1)).toMatchObject({
      club: "Galatasaray SK",
      probability: 0.6,
    });
  });

  it("rejects an invalid payload at the boundary", () => {
    expect(() =>
      validateDashboardPayload({ ...payload, schema_version: 2 }),
    ).toThrow(/schema/i);
  });
});
