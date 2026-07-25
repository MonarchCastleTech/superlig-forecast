import type { FixtureRow } from "./dashboard-data";

export type IndexedFixture = {
  home: number;
  away: number;
  homeExpectedGoals: number;
  awayExpectedGoals: number;
};

export type IndexedStartingState = {
  points: number;
  goalsFor: number;
  goalsAgainst: number;
};

export type TeamSimulationSnapshot = {
  club: string;
  positionCounts: number[];
  pointSum: number;
  goalDifferenceSum: number;
};

export type SimulationSnapshot = {
  simulations: number;
  elapsedMs: number;
  teams: TeamSimulationSnapshot[];
};

export type SimulationAccumulator = {
  simulations: number;
  rngState: number;
  positionCounts: Float64Array;
  pointSums: Float64Array;
  goalDifferenceSums: Float64Array;
  startingPoints: Int32Array;
  startingGoalsFor: Int32Array;
  startingGoalsAgainst: Int32Array;
};

const ZERO_SEED_FALLBACK = 0x6d2b79f5;

export function prepareFixtures(
  teams: string[],
  fixtures: FixtureRow[],
): IndexedFixture[] {
  const teamIndex = new Map(teams.map((team, index) => [team, index]));
  return fixtures.map((fixture) => {
    if (
      fixture.home_expected_goals === null ||
      fixture.away_expected_goals === null
    ) {
      throw new Error("Live simulation requires expected goals for every fixture");
    }
    const home = teamIndex.get(fixture.home_team);
    const away = teamIndex.get(fixture.away_team);
    if (home === undefined || away === undefined) {
      throw new Error("Fixture references a team outside the forecast table");
    }
    return {
      home,
      away,
      homeExpectedGoals: fixture.home_expected_goals,
      awayExpectedGoals: fixture.away_expected_goals,
    };
  });
}

export function createAccumulator(
  teamCount: number,
  seed: number,
  initial?: IndexedStartingState[],
): SimulationAccumulator {
  if (!Number.isInteger(teamCount) || teamCount < 2) {
    throw new Error("Live simulation requires at least two teams");
  }
  const normalizedSeed = seed >>> 0;
  if (initial !== undefined && initial.length !== teamCount) {
    throw new Error("Starting table must contain one row per team");
  }
  return {
    simulations: 0,
    rngState: normalizedSeed || ZERO_SEED_FALLBACK,
    positionCounts: new Float64Array(teamCount * teamCount),
    pointSums: new Float64Array(teamCount),
    goalDifferenceSums: new Float64Array(teamCount),
    startingPoints: Int32Array.from(
      initial?.map((row) => row.points) ?? new Array(teamCount).fill(0),
    ),
    startingGoalsFor: Int32Array.from(
      initial?.map((row) => row.goalsFor) ?? new Array(teamCount).fill(0),
    ),
    startingGoalsAgainst: Int32Array.from(
      initial?.map((row) => row.goalsAgainst) ?? new Array(teamCount).fill(0),
    ),
  };
}

function nextRandom(state: { value: number }): number {
  let value = state.value >>> 0;
  value ^= value << 13;
  value ^= value >>> 17;
  value ^= value << 5;
  state.value = value >>> 0;
  return state.value / 0x1_0000_0000;
}

function samplePoisson(lambda: number, state: { value: number }): number {
  if (!Number.isFinite(lambda) || lambda < 0) {
    throw new Error("Expected goals must be finite and non-negative");
  }
  if (lambda === 0) return 0;

  const threshold = Math.exp(-lambda);
  let product = 1;
  let draws = 0;
  do {
    draws += 1;
    product *= nextRandom(state);
  } while (product > threshold);
  return draws - 1;
}

export function simulateBatch(
  state: SimulationAccumulator,
  fixtures: IndexedFixture[],
  count: number,
): SimulationAccumulator {
  if (!Number.isSafeInteger(count) || count < 0) {
    throw new Error("Simulation count must be a non-negative safe integer");
  }
  if (state.simulations + count > Number.MAX_SAFE_INTEGER) {
    throw new Error("Simulation count exceeds JavaScript safe integer range");
  }

  const teamCount = state.pointSums.length;
  const positionCounts = new Float64Array(state.positionCounts);
  const pointSums = new Float64Array(state.pointSums);
  const goalDifferenceSums = new Float64Array(state.goalDifferenceSums);
  const rng = { value: state.rngState >>> 0 };

  for (let simulation = 0; simulation < count; simulation += 1) {
    const points = new Int32Array(state.startingPoints);
    const goalsFor = new Int32Array(state.startingGoalsFor);
    const goalsAgainst = new Int32Array(state.startingGoalsAgainst);

    for (const fixture of fixtures) {
      const homeGoals = samplePoisson(fixture.homeExpectedGoals, rng);
      const awayGoals = samplePoisson(fixture.awayExpectedGoals, rng);
      goalsFor[fixture.home] += homeGoals;
      goalsAgainst[fixture.home] += awayGoals;
      goalsFor[fixture.away] += awayGoals;
      goalsAgainst[fixture.away] += homeGoals;

      if (homeGoals > awayGoals) {
        points[fixture.home] += 3;
      } else if (awayGoals > homeGoals) {
        points[fixture.away] += 3;
      } else {
        points[fixture.home] += 1;
        points[fixture.away] += 1;
      }
    }

    const order = Array.from({ length: teamCount }, (_, index) => index);
    order.sort((left, right) => {
      const pointDifference = points[right] - points[left];
      if (pointDifference !== 0) return pointDifference;
      const leftGoalDifference = goalsFor[left] - goalsAgainst[left];
      const rightGoalDifference = goalsFor[right] - goalsAgainst[right];
      if (rightGoalDifference !== leftGoalDifference) {
        return rightGoalDifference - leftGoalDifference;
      }
      if (goalsFor[right] !== goalsFor[left]) {
        return goalsFor[right] - goalsFor[left];
      }
      return left - right;
    });

    for (let position = 0; position < order.length; position += 1) {
      const team = order[position];
      positionCounts[team * teamCount + position] += 1;
    }
    for (let team = 0; team < teamCount; team += 1) {
      pointSums[team] += points[team];
      goalDifferenceSums[team] += goalsFor[team] - goalsAgainst[team];
    }
  }

  return {
    simulations: state.simulations + count,
    rngState: rng.value,
    positionCounts,
    pointSums,
    goalDifferenceSums,
    startingPoints: state.startingPoints,
    startingGoalsFor: state.startingGoalsFor,
    startingGoalsAgainst: state.startingGoalsAgainst,
  };
}

export function toSnapshot(
  state: SimulationAccumulator,
  teams: string[],
  elapsedMs: number,
): SimulationSnapshot {
  if (teams.length !== state.pointSums.length) {
    throw new Error("Team labels do not match the simulation accumulator");
  }
  return {
    simulations: state.simulations,
    elapsedMs,
    teams: teams.map((club, team) => ({
      club,
      positionCounts: Array.from(
        state.positionCounts.slice(
          team * teams.length,
          (team + 1) * teams.length,
        ),
      ),
      pointSum: state.pointSums[team],
      goalDifferenceSum: state.goalDifferenceSums[team],
    })),
  };
}
