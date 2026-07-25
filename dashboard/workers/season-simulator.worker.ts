import {
  createAccumulator,
  simulateBatch,
  toSnapshot,
  type SimulationAccumulator,
} from "../lib/live-simulation";
import {
  nextBatchSize,
  type RunMode,
  type RunnerStatus,
  type StartCommand,
  type WorkerCommand,
  type WorkerEvent,
} from "../lib/live-worker-protocol";

let runId = "";
let status: RunnerStatus = "idle";
let mode: RunMode = { infinite: false, target: 1 };
let teams: string[] = [];
let fixtures: StartCommand["fixtures"] = [];
let accumulator: SimulationAccumulator | null = null;
let startedAt = 0;
let lastProgressAt = 0;

function emit(event: WorkerEvent) {
  self.postMessage(event);
}

function emitState() {
  emit({ type: "state", runId, status });
}

function emitProgress(now = performance.now()) {
  if (!accumulator) return;
  emit({
    type: "progress",
    runId,
    snapshot: toSnapshot(accumulator, teams, now - startedAt),
  });
  lastProgressAt = now;
}

function fail(reason: unknown) {
  status = "error";
  emit({
    type: "error",
    runId,
    message: reason instanceof Error ? reason.message : "Simulation worker failed",
  });
}

function schedule() {
  if (status !== "running") return;
  setTimeout(runNextBatch, 0);
}

function runNextBatch() {
  if (status !== "running" || !accumulator) return;
  try {
    const count = nextBatchSize({
      simulations: accumulator.simulations,
      ...mode,
    });
    if (count === 0) {
      emitProgress();
      status = "complete";
      emitState();
      return;
    }

    accumulator = simulateBatch(accumulator, fixtures, count);
    const now = performance.now();
    const complete =
      !mode.infinite && accumulator.simulations >= mode.target;
    if (complete || now - lastProgressAt >= 100) {
      emitProgress(now);
    }
    if (complete) {
      status = "complete";
      emitState();
      return;
    }
    schedule();
  } catch (reason) {
    fail(reason);
  }
}

function start(command: StartCommand) {
  runId = command.runId;
  mode = command.mode;
  teams = [...command.teams];
  fixtures = command.fixtures.map((fixture) => ({ ...fixture }));
  accumulator = createAccumulator(teams.length, command.seed);
  startedAt = performance.now();
  lastProgressAt = 0;
  status = "running";
  emitState();
  schedule();
}

self.onmessage = (message: MessageEvent<WorkerCommand>) => {
  const command = message.data;
  if (command.type === "start") {
    start(command);
    return;
  }
  if (command.runId !== runId) return;

  if (command.type === "pause" && status === "running") {
    status = "paused";
    emitProgress();
    emitState();
  } else if (command.type === "resume" && status === "paused") {
    status = "running";
    emitState();
    schedule();
  } else if (command.type === "stop" && status !== "idle") {
    status = "stopped";
    emitProgress();
    emitState();
  } else if (command.type === "reset") {
    status = "idle";
    accumulator = null;
    teams = [];
    fixtures = [];
    emitState();
  }
};
