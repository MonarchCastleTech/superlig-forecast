import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";

import type { FixtureRow } from "@/lib/dashboard-data";
import { MatchOutlook } from "./match-outlook";

afterEach(cleanup);

const fixture: FixtureRow = {
  home_team: "Galatasaray SK",
  away_team: "Fenerbahçe SK",
  home_expected_goals: 1.8,
  away_expected_goals: 1.1,
  home_win_probability: 0.56,
  draw_probability: 0.24,
  away_win_probability: 0.2,
};

test("shows a likely winner with all three outcome probabilities", () => {
  render(<MatchOutlook fixtures={[fixture]} />);

  expect(
    screen.getByText("Galatasaray SK most likely winner"),
  ).toBeVisible();
  expect(screen.getByText("Clear model edge")).toBeVisible();
  expect(screen.getByText("Home")).toBeVisible();
  expect(screen.getByText("Draw")).toBeVisible();
  expect(screen.getByText("Away")).toBeVisible();
  expect(screen.queryByText(/score prediction/i)).not.toBeInTheDocument();
});

test("calls a fixture with a narrow edge too close to call", () => {
  render(
    <MatchOutlook
      fixtures={[
        {
          ...fixture,
          home_win_probability: 0.36,
          draw_probability: 0.34,
          away_win_probability: 0.3,
        },
      ]}
    />,
  );

  expect(screen.getByText("Too close to call")).toBeVisible();
});
