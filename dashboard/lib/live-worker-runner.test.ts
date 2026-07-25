import { afterEach, expect, test, vi } from "vitest";
import type { WorkerEvent } from "./live-worker-protocol";
import { SeasonSimulationRunner } from "./live-worker-runner";

afterEach(() => {
  vi.useRealTimers();
});

test("infinite runner pauses, resumes, and stops between yielded batches", async () => {
  vi.useFakeTimers();
  const events: WorkerEvent[] = [];
  let clock = 0;
  const runner = new SeasonSimulationRunner(
    (event) => events.push(event),
    () => {
      clock += 120;
      return clock;
    },
  );

  runner.handle({
    type: "start",
    runId: "infinite-1",
    mode: { infinite: true, target: null },
    seed: 42,
    teams: ["A", "B"],
    fixtures: [
      {
        home: 0,
        away: 1,
        homeExpectedGoals: 1.4,
        awayExpectedGoals: 0.9,
      },
    ],
  });
  for (let batch = 0; batch < 4; batch += 1) {
    await vi.advanceTimersToNextTimerAsync();
  }

  runner.handle({ type: "pause", runId: "infinite-1" });
  const pausedCount = events
    .filter((event) => event.type === "progress")
    .at(-1)?.snapshot.simulations;
  await vi.advanceTimersToNextTimerAsync();
  expect(
    events.filter((event) => event.type === "progress").at(-1)?.snapshot
      .simulations,
  ).toBe(pausedCount);

  runner.handle({ type: "resume", runId: "infinite-1" });
  await vi.advanceTimersToNextTimerAsync();
  runner.handle({ type: "stop", runId: "infinite-1" });
  const stoppedCount = events
    .filter((event) => event.type === "progress")
    .at(-1)?.snapshot.simulations;
  expect(stoppedCount).toBeGreaterThan(pausedCount ?? 0);

  await vi.advanceTimersToNextTimerAsync();
  expect(
    events.filter((event) => event.type === "progress").at(-1)?.snapshot
      .simulations,
  ).toBe(stoppedCount);
});
