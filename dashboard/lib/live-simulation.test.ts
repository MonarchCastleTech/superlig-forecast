import { describe, expect, test } from "vitest";
import {
  createAccumulator,
  prepareFixtures,
  simulateBatch,
  toSnapshot,
} from "./live-simulation";

const teams = ["A", "B", "C"];
const fixtures = prepareFixtures(teams, [
  {
    home_team: "A",
    away_team: "B",
    home_expected_goals: 1.5,
    away_expected_goals: 0.8,
    home_win_probability: 0.54,
    draw_probability: 0.27,
    away_win_probability: 0.19,
  },
  {
    home_team: "B",
    away_team: "C",
    home_expected_goals: 1.1,
    away_expected_goals: 1.0,
    home_win_probability: 0.39,
    draw_probability: 0.31,
    away_win_probability: 0.3,
  },
]);

describe("live season simulation", () => {
  test("reproduces a seeded run across batch boundaries", () => {
    const oneBatch = simulateBatch(createAccumulator(3, 42), fixtures, 200);
    const split = simulateBatch(
      simulateBatch(createAccumulator(3, 42), fixtures, 75),
      fixtures,
      125,
    );
    expect(toSnapshot(split, teams, 1)).toEqual(
      toSnapshot(oneBatch, teams, 1),
    );
  });

  test("assigns every team to exactly one position per season", () => {
    const snapshot = toSnapshot(
      simulateBatch(createAccumulator(3, 7), fixtures, 100),
      teams,
      10,
    );
    for (const team of snapshot.teams) {
      expect(
        team.positionCounts.reduce((sum, value) => sum + value, 0),
      ).toBe(100);
    }
    for (let position = 0; position < 3; position += 1) {
      expect(
        snapshot.teams.reduce(
          (sum, team) => sum + team.positionCounts[position],
          0,
        ),
      ).toBe(100);
    }
  });

  test("rejects fixtures without expected goals", () => {
    expect(() =>
      prepareFixtures(teams, [
        {
          home_team: "A",
          away_team: "B",
          home_expected_goals: null,
          away_expected_goals: 0.8,
          home_win_probability: 0.54,
          draw_probability: 0.27,
          away_win_probability: 0.19,
        },
      ]),
    ).toThrow("Live simulation requires expected goals for every fixture");
  });

  test("rejects a batch beyond the safe integer range", () => {
    const accumulator = {
      ...createAccumulator(3, 42),
      simulations: Number.MAX_SAFE_INTEGER,
    };
    expect(() => simulateBatch(accumulator, fixtures, 1)).toThrow(
      "Simulation count exceeds JavaScript safe integer range",
    );
  });
});
