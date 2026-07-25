import {
  createAccumulator,
  simulateBatch,
  toSnapshot,
  type SimulationAccumulator,
} from "./live-simulation";
import {
  nextBatchSize,
  type RunMode,
  type RunnerStatus,
  type StartCommand,
  type WorkerCommand,
  type WorkerEvent,
} from "./live-worker-protocol";

type Emit = (event: WorkerEvent) => void;
type Now = () => number;
type Schedule = (task: () => void) => unknown;

export class SeasonSimulationRunner {
  private runId = "";
  private status: RunnerStatus = "idle";
  private mode: RunMode = { infinite: false, target: 1 };
  private teams: string[] = [];
  private fixtures: StartCommand["fixtures"] = [];
  private accumulator: SimulationAccumulator | null = null;
  private startedAt = 0;
  private lastProgressAt = 0;

  constructor(
    private readonly emit: Emit,
    private readonly now: Now = () => performance.now(),
    private readonly scheduleTask: Schedule = (task) => setTimeout(task, 0),
  ) {}

  handle(command: WorkerCommand): void {
    if (command.type === "start") {
      this.start(command);
      return;
    }
    if (command.runId !== this.runId) return;

    if (command.type === "pause" && this.status === "running") {
      this.status = "paused";
      this.emitProgress();
      this.emitState();
    } else if (command.type === "resume" && this.status === "paused") {
      this.status = "running";
      this.emitState();
      this.schedule();
    } else if (command.type === "stop" && this.status !== "idle") {
      this.status = "stopped";
      this.emitProgress();
      this.emitState();
    } else if (command.type === "reset") {
      this.status = "idle";
      this.accumulator = null;
      this.teams = [];
      this.fixtures = [];
      this.emitState();
    }
  }

  private emitState(): void {
    this.emit({
      type: "state",
      runId: this.runId,
      status: this.status,
    });
  }

  private emitProgress(now = this.now()): void {
    if (!this.accumulator) return;
    this.emit({
      type: "progress",
      runId: this.runId,
      snapshot: toSnapshot(
        this.accumulator,
        this.teams,
        now - this.startedAt,
      ),
    });
    this.lastProgressAt = now;
  }

  private fail(reason: unknown): void {
    this.status = "error";
    this.emit({
      type: "error",
      runId: this.runId,
      message:
        reason instanceof Error ? reason.message : "Simulation worker failed",
    });
  }

  private schedule(): void {
    if (this.status !== "running") return;
    this.scheduleTask(() => this.runNextBatch());
  }

  private runNextBatch(): void {
    if (this.status !== "running" || !this.accumulator) return;
    try {
      const count = nextBatchSize({
        simulations: this.accumulator.simulations,
        ...this.mode,
      });
      if (count === 0) {
        this.emitProgress();
        this.status = "complete";
        this.emitState();
        return;
      }

      this.accumulator = simulateBatch(
        this.accumulator,
        this.fixtures,
        count,
      );
      const now = this.now();
      const complete =
        !this.mode.infinite &&
        this.accumulator.simulations >= this.mode.target;
      if (complete || now - this.lastProgressAt >= 100) {
        this.emitProgress(now);
      }
      if (complete) {
        this.status = "complete";
        this.emitState();
        return;
      }
      this.schedule();
    } catch (reason) {
      this.fail(reason);
    }
  }

  private start(command: StartCommand): void {
    this.runId = command.runId;
    this.mode = command.mode;
    this.teams = [...command.teams];
    this.fixtures = command.fixtures.map((fixture) => ({ ...fixture }));
    this.accumulator = createAccumulator(
      this.teams.length,
      command.seed,
      command.startingTable,
    );
    this.startedAt = this.now();
    this.lastProgressAt = 0;
    this.status = "running";
    this.emitState();
    this.schedule();
  }
}
