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
  /** Optional for compatibility with older published dashboard snapshots. */
  predicted?: boolean;
};

export type MatchOutcome = {
  outcome: "home" | "draw" | "away";
  label: string;
  confidence: "Too close to call" | "Slight edge" | "Clear model edge";
};

export type CurrentTableRow = {
  club: string;
  points: number;
  goals_for: number;
  goals_against: number;
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
    completed_fixture_count?: number;
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
  freshness: {
    generated_at: string;
    match_snapshot_at: string;
    squad_snapshot_at: string;
    valuation_snapshot_at: string;
    latest_match_date: string | null;
    source_status: "fresh" | "stale" | "failed";
    source_notes: string[];
  };
  championship: ChampionshipRow[];
  convergence: ConvergenceRow[];
  fixtures: FixtureRow[];
  positions: PositionRow[];
  expected_standings: ExpectedStanding[];
  publication_history?: Array<{
    generated_at: string;
    probabilities: Record<string, number>;
  }>;
  current_table?: CurrentTableRow[];
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
    !isRecord(value.freshness) ||
    typeof value.freshness.generated_at !== "string" ||
    typeof value.freshness.match_snapshot_at !== "string" ||
    typeof value.freshness.squad_snapshot_at !== "string" ||
    typeof value.freshness.valuation_snapshot_at !== "string" ||
    (value.freshness.latest_match_date !== null &&
      typeof value.freshness.latest_match_date !== "string") ||
    !["fresh", "stale", "failed"].includes(
      String(value.freshness.source_status),
    ) ||
    !Array.isArray(value.freshness.source_notes) ||
    !value.freshness.source_notes.every(
      (note) => typeof note === "string",
    )
  ) {
    throw new Error("Dashboard freshness is incomplete");
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
  if (
    value.fixtures.some(
      (row) =>
        !isRecord(row) ||
        (row.predicted !== undefined && typeof row.predicted !== "boolean"),
    )
  ) {
    throw new Error("Dashboard contains an invalid prediction status");
  }
  if (
    value.publication_history !== undefined &&
    (!Array.isArray(value.publication_history) ||
      !value.publication_history.every(
        (entry) =>
          isRecord(entry) &&
          typeof entry.generated_at === "string" &&
          isRecord(entry.probabilities) &&
          Object.values(entry.probabilities).every(isProbability),
      ))
  ) {
    throw new Error("Dashboard publication history is invalid");
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

export function classifyMatchOutcome(fixture: FixtureRow): MatchOutcome {
  const outcomes = [
    { outcome: "home" as const, probability: fixture.home_win_probability },
    { outcome: "draw" as const, probability: fixture.draw_probability },
    { outcome: "away" as const, probability: fixture.away_win_probability },
  ].sort((left, right) => right.probability - left.probability);
  const best = outcomes[0];
  const margin = best.probability - outcomes[1].probability;
  const label =
    best.outcome === "draw"
      ? "Draw most likely"
      : `${
          best.outcome === "home" ? fixture.home_team : fixture.away_team
        } most likely winner`;
  return {
    outcome: best.outcome,
    label,
    confidence:
      margin < 0.05
        ? "Too close to call"
        : margin <= 0.12
          ? "Slight edge"
          : "Clear model edge",
  };
}

export function formatForecastUpdate(value: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Europe/Istanbul",
    timeZoneName: "short",
  }).format(new Date(value));
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
