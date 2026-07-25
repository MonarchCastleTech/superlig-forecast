import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import type { DashboardPayload } from "@/lib/dashboard-data";
import type { LiveSimulationController } from "@/hooks/use-live-simulation";
import { LiveSimulationPanel } from "./live-simulation-panel";

const data = {
  meta: { team_count: 18, seed: 2607 },
  championship: [
    { club: "Galatasaray" },
    { club: "Fenerbahçe" },
    { club: "Beşiktaş" },
  ],
} as DashboardPayload;

test("switches between a finite target and an infinite live run", async () => {
  const user = userEvent.setup();
  const controller: LiveSimulationController = {
    status: "idle",
    snapshot: null,
    history: [],
    error: null,
    start: vi.fn(),
    pause: vi.fn(),
    resume: vi.fn(),
    stop: vi.fn(),
    reset: vi.fn(),
  };

  render(<LiveSimulationPanel data={data} controller={controller} />);

  expect(screen.getByLabelText("Simulation target")).toHaveValue(100000);
  await user.click(
    screen.getByRole("checkbox", { name: "Run until stopped" }),
  );
  expect(screen.getByLabelText("Simulation target")).toBeDisabled();
  await user.click(screen.getByRole("button", { name: "Play simulation" }));
  expect(controller.start).toHaveBeenCalledWith(
    { infinite: true, target: null },
    expect.any(Number),
  );
});
