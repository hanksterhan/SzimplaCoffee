import { createFileRoute } from "@tanstack/react-router";
import { useDashboard } from "@/hooks/use-dashboard";
import { MetricsGrid } from "@/components/dashboard/MetricsGrid";
import { MerchantOverviewTable } from "@/components/dashboard/MerchantOverviewTable";

export const Route = createFileRoute("/")({
  component: DashboardPage,
});

function DashboardPage() {
  const { data: stats, isLoading } = useDashboard();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">☕ Dashboard</h1>
        <p className="text-muted-foreground">SzimplaCoffee sourcing overview</p>
      </div>
      <MetricsGrid stats={stats} loading={isLoading} />
      <MerchantOverviewTable />
    </div>
  );
}
