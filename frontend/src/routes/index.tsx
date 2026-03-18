import { createFileRoute } from "@tanstack/react-router";
import { useDashboard } from "@/hooks/use-dashboard";
import { useCrawlDue, useRunDueCrawls } from "@/hooks/use-crawl-schedule";
import { MetricsGrid } from "@/components/dashboard/MetricsGrid";
import { MetadataFillRate } from "@/components/dashboard/MetadataFillRate";
import { MerchantOverviewTable } from "@/components/dashboard/MerchantOverviewTable";

export const Route = createFileRoute("/")({
  component: DashboardPage,
});

function CrawlStatusBanner() {
  const { data: due, isLoading } = useCrawlDue();
  const { mutate: runDue, isPending, data: result } = useRunDueCrawls();

  if (isLoading) return null;
  const count = due?.length ?? 0;

  const bgColor =
    count === 0
      ? "bg-green-50 border-green-200 text-green-800"
      : count <= 3
        ? "bg-yellow-50 border-yellow-200 text-yellow-800"
        : "bg-red-50 border-red-200 text-red-800";

  return (
    <div
      className={`flex items-center justify-between rounded-lg border px-4 py-3 text-sm ${bgColor}`}
    >
      <div className="flex items-center gap-2">
        <span className="text-lg">{count === 0 ? "✅" : count <= 3 ? "⚠️" : "🔴"}</span>
        <span>
          {count === 0
            ? "All merchants are up to date"
            : `${count} merchant${count === 1 ? "" : "s"} due for crawl`}
        </span>
        {result && (
          <span className="opacity-70">
            — {result.triggered} crawl{result.triggered === 1 ? "" : "s"} triggered
          </span>
        )}
      </div>
      {count > 0 && (
        <button
          onClick={() => runDue()}
          disabled={isPending}
          className="ml-4 rounded bg-white px-3 py-1 font-medium shadow-sm hover:bg-gray-50 disabled:opacity-50 border border-current"
        >
          {isPending ? "Starting…" : "Crawl All Due"}
        </button>
      )}
    </div>
  );
}

function DashboardPage() {
  const { data: stats, isLoading } = useDashboard();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">☕ Dashboard</h1>
        <p className="text-muted-foreground">SzimplaCoffee sourcing overview</p>
      </div>
      <MetricsGrid stats={stats} loading={isLoading} />
      <MetadataFillRate stats={stats} loading={isLoading} />
      <CrawlStatusBanner />
      <MerchantOverviewTable />
    </div>
  );
}
