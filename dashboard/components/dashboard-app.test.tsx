import "@testing-library/jest-dom/vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";
import { validateDashboardPayload } from "@/lib/dashboard-data";
import { DashboardApp } from "./dashboard-app";

afterEach(cleanup);

test("shows MCT branding in the masthead and footer", () => {
  const payload = validateDashboardPayload(
    JSON.parse(
      readFileSync(
        join(process.cwd(), "public", "data", "dashboard.json"),
        "utf8",
      ),
    ),
  );
  render(<DashboardApp data={payload} />);
  expect(
    screen.getAllByRole("img", {
      name: "Monarch Castle Technologies",
    }),
  ).toHaveLength(2);
});

test("presents one published forecast without simulator controls", () => {
  const payload = validateDashboardPayload(
    JSON.parse(
      readFileSync(
        join(process.cwd(), "public", "data", "dashboard.json"),
        "utf8",
      ),
    ),
  );

  render(<DashboardApp data={payload} />);

  expect(screen.getByTestId("forecast-updated")).toHaveTextContent("Updated");
  expect(screen.getByRole("note")).toHaveTextContent("not betting advice");
  expect(screen.getByRole("note")).toHaveTextContent("not a guarantee");
  expect(screen.queryByText(/simulation target/i)).not.toBeInTheDocument();
  expect(
    screen.queryByRole("button", { name: /play simulation/i }),
  ).not.toBeInTheDocument();
});

test("exposes the title forecast and possible table accessibly", () => {
  const payload = validateDashboardPayload(
    JSON.parse(
      readFileSync(
        join(process.cwd(), "public", "data", "dashboard.json"),
        "utf8",
      ),
    ),
  );

  render(<DashboardApp data={payload} />);

  expect(
    screen.getByRole("heading", { name: /title forecast/i }),
  ).toBeVisible();
  expect(screen.getByText(/model probability/i)).toBeVisible();
  expect(
    screen.getByRole("table", { name: /possible final table/i }),
  ).toBeVisible();
  expect(screen.getAllByText(/expected points/i).length).toBeGreaterThan(0);
});

test("publishes an academic methodology and explains validation metrics", () => {
  const payload = validateDashboardPayload(
    JSON.parse(
      readFileSync(
        join(process.cwd(), "public", "data", "dashboard.json"),
        "utf8",
      ),
    ),
  );

  render(<DashboardApp data={payload} />);

  for (const section of [
    "Forecast target",
    "Data provenance",
    "Temporal integrity",
    "Structural model",
    "Market-value adjustment",
    "Current-season state",
    "Monte Carlo estimation",
    "Backtest design",
    "Uncertainty",
    "Limitations",
  ]) {
    expect(screen.getByRole("heading", { name: section })).toBeVisible();
  }
  expect(screen.getByText(/log loss penalizes/i)).toBeVisible();
  expect(screen.getByText(/brier score measures/i)).toBeVisible();
});
