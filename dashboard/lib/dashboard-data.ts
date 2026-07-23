export type ChampionshipRow = {
  club: string;
  squad_value_eur: number | null;
  champion_count: number;
  champion_probability: number;
  ci95_half_width: number;
};

export type ConvergenceRow = {
  simulation_count: number;
  club: string;
  champion_probability: number;
};

export type FixtureRow = {
  home_team: string;
  away_team: string;
  home_expected_goals: number | null;
  away_expected_goals: number | null;
  home_win_probability: number;
  draw_probability: number;
  away_win_probability: number;
};

export type PositionRow = {
  club: string;
  position: number;
  count: number;
  probability: number;
};

export type ExpectedStanding = {
  club: string;
  expected_position: number;
  median_position: number;
  most_likely_position: number;
  expected_points: number;
  expected_goal_difference: number;
  top_four_probability: number;
  position_17_probability: number | null;
  relegation_probability: number;
};

export type BacktestFold = {
  season: number;
  match_count: number;
  market_match_count: number;
  scores: Record<string, number | null>;
};

export type DashboardPayload = {
  schema_version: 1;
  meta: {
    season: string;
    simulations: number;
    seed: number;
    model_version: string;
    team_count: number;
    fixture_count: number;
    checkpoints: number[];
    value_coefficient: number;
    source_alignment: {
      official_team_count: number;
      market_team_count: number;
      matched_team_count: number;
      official_only: string[];
      market_only: string[];
    } | null;
  };
  championship: ChampionshipRow[];
  convergence: ConvergenceRow[];
  fixtures: FixtureRow[];
  positions: PositionRow[];
  expected_standings: ExpectedStanding[];
  backtest: {
    method: string;
    start_season: number;
    end_season: number;
    market_weight: number;
    fold_count: number;
    match_count: number;
    market_match_count: number;
    aggregate: Record<string, number | null>;
    folds: BacktestFold[];
    acceptance: {
      passed: boolean;
      checks: Record<string, boolean>;
    };
  };
  position_backtest: {
    method: string;
    start_season: number;
    end_season: number;
    fold_count: number;
    simulations_per_fold: number;
    aggregate: Record<string, number>;
    folds: Array<{
      season: number;
      team_count: number;
      match_count: number;
      simulations: number;
      scores: Record<string, number>;
      teams: Array<{
        team: string;
        actual_position: number;
        expected_position: number;
        median_position: number;
        most_likely_position: number;
        actual_position_probability: number;
        expected_points: number;
        expected_goal_difference: number;
        position_probabilities: number[];
      }>;
    }>;
    acceptance: {
      passed: boolean;
      checks: Record<string, boolean>;
    };
  };
};

export type OutcomeFilter = "all" | "home" | "draw" | "away";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isProbability(value: unknown): value is number {
  return (
    typeof value === "number" &&
    Number.isFinite(value) &&
    value >= 0 &&
    value <= 1
  );
}

export function validateDashboardPayload(value: unknown): DashboardPayload {
  if (!isRecord(value) || value.schema_version !== 1) {
    throw new Error("Unsupported dashboard schema");
  }
  if (
    !isRecord(value.meta) ||
    typeof value.meta.season !== "string" ||
    typeof value.meta.simulations !== "number" ||
    !Array.isArray(value.meta.checkpoints)
  ) {
    throw new Error("Dashboard metadata is incomplete");
  }
  if (
    !Array.isArray(value.championship) ||
    !Array.isArray(value.convergence) ||
    !Array.isArray(value.fixtures) ||
    !Array.isArray(value.positions) ||
    !Array.isArray(value.expected_standings) ||
    !isRecord(value.backtest) ||
    !isRecord(value.position_backtest)
  ) {
    throw new Error("Dashboard sections are incomplete");
  }

  const probabilityValues = [
    ...value.championship.flatMap((row) =>
      isRecord(row) ? [row.champion_probability, row.ci95_half_width] : [NaN],
    ),
    ...value.convergence.map((row) =>
      isRecord(row) ? row.champion_probability : NaN,
    ),
    ...value.fixtures.flatMap((row) =>
      isRecord(row)
        ? [
            row.home_win_probability,
            row.draw_probability,
            row.away_win_probability,
          ]
        : [NaN],
    ),
    ...value.positions.map((row) =>
      isRecord(row) ? row.probability : NaN,
    ),
    ...value.expected_standings.flatMap((row) =>
      isRecord(row)
        ? [
            row.top_four_probability,
            row.position_17_probability ?? 0,
            row.relegation_probability,
          ]
        : [NaN],
    ),
  ];
  if (!probabilityValues.every(isProbability)) {
    throw new Error("Dashboard contains an invalid probability");
  }
  return value as DashboardPayload;
}

export function rankAtCheckpoint(
  payload: DashboardPayload,
  checkpoint: number,
): ChampionshipRow[] {
  const probabilities = new Map(
    payload.convergence
      .filter((row) => row.simulation_count === checkpoint)
      .map((row) => [row.club, row.champion_probability]),
  );
  return payload.championship
    .map((row) => ({
      ...row,
      champion_probability:
        probabilities.get(row.club) ?? row.champion_probability,
    }))
    .sort((left, right) => {
      return right.champion_probability - left.champion_probability;
    });
}

export function filterFixtures(
  fixtures: FixtureRow[],
  query: string,
  outcome: OutcomeFilter,
): FixtureRow[] {
  const needle = query.trim().toLocaleLowerCase("tr-TR");
  return fixtures.filter((fixture) => {
    const matchesClub =
      needle.length === 0 ||
      fixture.home_team.toLocaleLowerCase("tr-TR").includes(needle) ||
      fixture.away_team.toLocaleLowerCase("tr-TR").includes(needle);
    if (!matchesClub || outcome === "all") {
      return matchesClub;
    }
    const strongest = Math.max(
      fixture.home_win_probability,
      fixture.draw_probability,
      fixture.away_win_probability,
    );
    return (
      (outcome === "home" && fixture.home_win_probability === strongest) ||
      (outcome === "draw" && fixture.draw_probability === strongest) ||
      (outcome === "away" && fixture.away_win_probability === strongest)
    );
  });
}

export function formatProbability(
  value: number | null | undefined,
  digits = 1,
): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "Not available";
  }
  return `${(value * 100).toFixed(digits)}%`;
}

export function positionDistribution(
  payload: DashboardPayload,
  club: string,
): PositionRow[] {
  return payload.positions
    .filter((row) => row.club === club)
    .sort((left, right) => left.position - right.position);
}

export function leaderAtPosition(
  payload: DashboardPayload,
  position: number,
): PositionRow | null {
  return (
    payload.positions
      .filter((row) => row.position === position)
      .sort((left, right) => right.probability - left.probability)[0] ?? null
  );
}

export function formatInteger(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

export function formatCurrency(value: number | null): string {
  if (value === null || !Number.isFinite(value)) {
    return "Not available";
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "EUR",
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}
