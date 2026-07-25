import "@testing-library/jest-dom/vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { validateDashboardPayload } from "@/lib/dashboard-data";
import { DashboardApp } from "./dashboard-app";

vi.mock("@/hooks/use-live-simulation", () => ({
  useLiveSimulation: () => ({
    status: "idle",
    snapshot: null,
    history: [],
    error: null,
    start: vi.fn(),
    pause: vi.fn(),
    resume: vi.fn(),
    stop: vi.fn(),
    reset: vi.fn(),
  }),
}));

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
