import { expect, test } from "vitest";
import type { ProgressEvent } from "./live-worker-protocol";
import {
  initialRunnerState,
  nextBatchSize,
  reduceWorkerEvent,
} from "./live-worker-protocol";

function progressEvent(runId: string): ProgressEvent {
  return {
    type: "progress",
    runId,
    snapshot: {
      simulations: 25,
      elapsedMs: 5,
      teams: [],
    },
  };
}

test("finite runs stop exactly at the requested target", () => {
  expect(
    nextBatchSize({ simulations: 990, target: 1_000, infinite: false }),
  ).toBe(10);
});

test("infinite runs always schedule another bounded batch", () => {
  expect(
    nextBatchSize({
      simulations: 5_000_000,
      target: null,
      infinite: true,
    }),
  ).toBeGreaterThan(0);
});

test("ignores progress from a stale run id", () => {
  const current = initialRunnerState("run-2");
  expect(reduceWorkerEvent(current, progressEvent("run-1"))).toEqual(current);
});
