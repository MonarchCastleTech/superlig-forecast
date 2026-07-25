import { useEffect, useState } from "react";
import { DashboardApp } from "@/components/dashboard-app";
import {
  type DashboardPayload,
  validateDashboardPayload,
} from "@/lib/dashboard-data";

export function AppLoader() {
  const [data, setData] = useState<DashboardPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const url = `${import.meta.env.BASE_URL}data/dashboard.json`;
    fetch(url)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Dashboard data returned ${response.status}`);
        }
        return response.json();
      })
      .then((value) => setData(validateDashboardPayload(value)))
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
  if (!data) {
    return <main className="load-state">Loading forecast data…</main>;
  }
  return <DashboardApp data={data} />;
}
