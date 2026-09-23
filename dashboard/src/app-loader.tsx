import { useEffect, useState } from "react";
import { DashboardApp } from "@/components/dashboard-app";
import {
  type DashboardPayload,
  validateDashboardPayload,
} from "@/lib/dashboard-data";

export function AppLoader() {
  const [data, setData] = useState<DashboardPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [withheld, setWithheld] = useState<string | null>(null);

  useEffect(() => {
    const url = `${import.meta.env.BASE_URL}data/dashboard.json`;
    fetch(url)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Dashboard data returned ${response.status}`);
        }
        return response.json();
      })
      .then((value: unknown) => {
        const payload = value as { meta?: { publication_status?: string; withdrawal_reason?: string } };
        if (payload?.meta?.publication_status === "WITHHELD") {
          setWithheld(payload.meta.withdrawal_reason || "The current forecast has been withheld because its source data did not pass publication checks.");
          return;
        }
        setData(validateDashboardPayload(value));
      })
      .catch((reason: unknown) =>
        setError(
          reason instanceof Error
            ? reason.message
            : "Dashboard data failed to load",
        ),
      );
  }, []);

  if (error) {
    return (
      <main className="load-state" role="alert">
        {error}
      </main>
    );
  }
  if (withheld) {
    return (
      <main className="load-state" role="alert">
        <h1>Forecast withheld</h1>
        <p>{withheld}</p>
        <p>The next forecast will appear after official results and all 18 squad records reconcile.</p>
        <a href={`${import.meta.env.BASE_URL}methodology/`}>Read the methodology</a>
      </main>
    );
  }
  if (!data) {
    return <main className="load-state">Loading forecast data…</main>;
  }
  return <DashboardApp data={data} />;
}
