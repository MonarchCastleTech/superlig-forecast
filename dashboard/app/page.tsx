import rawDashboardData from "@/public/data/dashboard.json";
import { DashboardApp } from "@/components/dashboard-app";
import { validateDashboardPayload } from "@/lib/dashboard-data";

const dashboardData = validateDashboardPayload(rawDashboardData);

export default function Home() {
  return <DashboardApp data={dashboardData} />;
}

