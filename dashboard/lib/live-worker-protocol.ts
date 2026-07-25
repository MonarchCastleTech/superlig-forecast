import type {
  IndexedFixture,
  IndexedStartingState,
  SimulationSnapshot,
} from "./live-simulation";

export type RunMode =
  | { infinite: true; target: null }
  | { infinite: false; target: number };

export type RunnerStatus =
  | "idle"
  | "running"
  | "paused"
  | "stopped"
  | "complete"
  | "error";

export type StartCommand = {
  type: "start";
  runId: string;
  mode: RunMode;
  seed: number;
  teams: string[];
  fixtures: IndexedFixture[];
  startingTable?: IndexedStartingState[];
};

export type PauseCommand = { type: "pause"; runId: string };
export type ResumeCommand = { type: "resume"; runId: string };
export type StopCommand = { type: "stop"; runId: string };
export type ResetCommand = { type: "reset"; runId: string };

export type WorkerCommand =
  | StartCommand
  | PauseCommand
  | ResumeCommand
  | StopCommand
  | ResetCommand;

export type ProgressEvent = {
  type: "progress";
  runId: string;
  snapshot: SimulationSnapshot;
};

export type StateEvent = {
  type: "state";
  runId: string;
  status: RunnerStatus;
};

export type ErrorEvent = {
  type: "error";
  runId: string;
  message: string;
};

export type WorkerEvent = ProgressEvent | StateEvent | ErrorEvent;

export type RunnerState = {
  runId: string;
  status: RunnerStatus;
  snapshot: SimulationSnapshot | null;
  error: string | null;
};

type BatchPosition = RunMode & { simulations: number };

export function nextBatchSize(position: BatchPosition): number {
  let batch = 10_000;
  if (position.simulations < 250) batch = 25;
  else if (position.simulations < 10_000) batch = 250;
  else if (position.simulations < 250_000) batch = 2_500;

  if (position.infinite) return batch;
  if (
    !Number.isSafeInteger(position.target) ||
    position.target <= 0 ||
    position.target > Number.MAX_SAFE_INTEGER
  ) {
    throw new Error("Finite simulation target must be a positive safe integer");
  }
  return Math.max(0, Math.min(batch, position.target - position.simulations));
}

export function initialRunnerState(runId: string): RunnerState {
  return {
    runId,
    status: "idle",
    snapshot: null,
    error: null,
  };
}

export function reduceWorkerEvent(
  state: RunnerState,
  event: WorkerEvent,
): RunnerState {
  if (event.runId !== state.runId) return state;
  if (event.type === "progress") {
    return { ...state, snapshot: event.snapshot };
  }
  if (event.type === "error") {
    return { ...state, status: "error", error: event.message };
  }
  return { ...state, status: event.status };
}
