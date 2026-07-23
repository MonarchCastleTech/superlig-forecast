import { describe, expect, it } from "vitest";

import {
  filterFixtures,
  formatProbability,
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

  it("rejects an invalid payload at the boundary", () => {
    expect(() =>
      validateDashboardPayload({ ...payload, schema_version: 2 }),
    ).toThrow(/schema/i);
  });
});

