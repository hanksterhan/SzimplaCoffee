import type { DashboardMetrics } from "@/hooks/use-dashboard";

interface MetadataFillRateProps {
  stats?: DashboardMetrics;
  loading: boolean;
}

function pct(numerator: number, denominator: number): string {
  if (denominator === 0) return "0%";
  return `${Math.round((numerator / denominator) * 100)}%`;
}

export function MetadataFillRate({ stats, loading }: MetadataFillRateProps) {
  if (loading || !stats) {
    return (
      <div className="rounded-lg border bg-card px-4 py-3 text-sm text-muted-foreground animate-pulse">
        Loading metadata fill rate…
      </div>
    );
  }

  const total = stats.total_products ?? 0;
  const originPct = pct(stats.products_with_origin ?? 0, total);
  const processPct = pct(stats.products_with_process ?? 0, total);
  const roastPct = pct(stats.products_with_roast_level ?? 0, total);

  return (
    <div className="rounded-lg border bg-card px-4 py-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-muted-foreground">
          📊 Metadata fill rate ({total} products)
        </span>
        <span className="text-sm text-muted-foreground">
          Origin: <span className="font-semibold text-foreground">{originPct}</span>
          {" | "}
          Process: <span className="font-semibold text-foreground">{processPct}</span>
          {" | "}
          Roast: <span className="font-semibold text-foreground">{roastPct}</span>
        </span>
      </div>
    </div>
  );
}
