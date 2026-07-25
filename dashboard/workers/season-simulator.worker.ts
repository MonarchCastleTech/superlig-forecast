import { SeasonSimulationRunner } from "../lib/live-worker-runner";
import type {
  WorkerCommand,
  WorkerEvent,
} from "../lib/live-worker-protocol";

const runner = new SeasonSimulationRunner((event: WorkerEvent) => {
  self.postMessage(event);
});

self.onmessage = (message: MessageEvent<WorkerCommand>) => {
  runner.handle(message.data);
};
