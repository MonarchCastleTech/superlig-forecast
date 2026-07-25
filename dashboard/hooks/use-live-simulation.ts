import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { DashboardPayload } from "@/lib/dashboard-data";
import {
  prepareFixtures,
  type SimulationSnapshot,
} from "@/lib/live-simulation";
import type {
  RunMode,
  RunnerStatus,
  WorkerCommand,
  WorkerEvent,
} from "@/lib/live-worker-protocol";

const MAX_HISTORY_POINTS = 600;

export type LiveSimulationController = {
  status: RunnerStatus;
  snapshot: SimulationSnapshot | null;
  history: SimulationSnapshot[];
  error: string | null;
  start: (mode: RunMode, seed: number) => void;
  pause: () => void;
  resume: () => void;
  stop: () => void;
  reset: () => void;
};

export function compactHistory(
  history: SimulationSnapshot[],
): SimulationSnapshot[] {
  if (history.length <= MAX_HISTORY_POINTS) return history;
  return Array.from({ length: MAX_HISTORY_POINTS }, (_, index) => {
    const sourceIndex = Math.round(
      (index * (history.length - 1)) / (MAX_HISTORY_POINTS - 1),
    );
    return history[sourceIndex];
  });
}

export function useLiveSimulation(
  data: DashboardPayload,
): LiveSimulationController {
  const workerRef = useRef<Worker | null>(null);
  const runIdRef = useRef("");
  const sequenceRef = useRef(0);
  const [status, setStatus] = useState<RunnerStatus>("idle");
  const [snapshot, setSnapshot] = useState<SimulationSnapshot | null>(null);
  const [history, setHistory] = useState<SimulationSnapshot[]>([]);
  const [error, setError] = useState<string | null>(null);

  const teams = useMemo(
    () => data.expected_standings.map((row) => row.club),
    [data.expected_standings],
  );
  const fixtures = useMemo(
    () => prepareFixtures(teams, data.fixtures),
    [data.fixtures, teams],
  );
  const startingTable = useMemo(() => {
    const rows = new Map(
      (data.current_table ?? []).map((row) => [row.club, row]),
    );
    return teams.map((team) => {
      const row = rows.get(team);
      return {
        points: row?.points ?? 0,
        goalsFor: row?.goals_for ?? 0,
        goalsAgainst: row?.goals_against ?? 0,
      };
    });
  }, [data.current_table, teams]);

  useEffect(() => {
    const worker = new Worker(
      new URL("../workers/season-simulator.worker.ts", import.meta.url),
      { type: "module" },
    );
    workerRef.current = worker;
    worker.onmessage = (message: MessageEvent<WorkerEvent>) => {
      const event = message.data;
      if (event.runId !== runIdRef.current) return;
      if (event.type === "progress") {
        setSnapshot(event.snapshot);
        setHistory((current) =>
          compactHistory([...current, event.snapshot]),
        );
      } else if (event.type === "state") {
        setStatus(event.status);
      } else {
        setStatus("error");
        setError(event.message);
      }
    };
    worker.onerror = () => {
      setStatus("error");
      setError("Simulation worker crashed");
    };
    return () => {
      worker.terminate();
      workerRef.current = null;
    };
  }, []);

  const post = useCallback((command: WorkerCommand) => {
    workerRef.current?.postMessage(command);
  }, []);

  const start = useCallback(
    (mode: RunMode, seed: number) => {
      sequenceRef.current += 1;
      const nextRunId = `run-${Date.now()}-${sequenceRef.current}`;
      runIdRef.current = nextRunId;
      setStatus("running");
      setSnapshot(null);
      setHistory([]);
      setError(null);
      post({
        type: "start",
        runId: nextRunId,
        mode,
        seed,
        teams,
        fixtures,
        startingTable,
      });
    },
    [fixtures, post, startingTable, teams],
  );

  const sendControl = useCallback(
    (type: "pause" | "resume" | "stop" | "reset") => {
      if (!runIdRef.current) return;
      post({ type, runId: runIdRef.current });
    },
    [post],
  );

  const reset = useCallback(() => {
    sendControl("reset");
    setStatus("idle");
    setSnapshot(null);
    setHistory([]);
    setError(null);
  }, [sendControl]);

  return {
    status,
    snapshot,
    history,
    error,
    start,
    pause: () => sendControl("pause"),
    resume: () => sendControl("resume"),
    stop: () => sendControl("stop"),
    reset,
  };
}
