import type { components } from "@/api/schema";
import type { DashboardMetrics } from "@/hooks/use-dashboard";

interface MetadataFillRateProps {
  stats?: DashboardMetrics;
  loading: boolean;
}

type MetadataFillRates = components["schemas"]["MetadataFillRates"];

function colorClass(pct: number): string {
  if (pct >= 70) return "text-green-600";
  if (pct >= 50) return "text-yellow-600";
  return "text-red-500";
}

function PctBadge({ label, pct }: { label: string; pct: number }) {
  return (
    <span className="text-sm">
      {label}:{" "}
      <span className={`font-semibold ${colorClass(pct)}`}>{pct}%</span>
    </span>
  );
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
  const fills: MetadataFillRates | undefined = stats.metadata_fill_rates;

  // Fallback: compute from raw counts if metadata_fill_rates not present
  const originPct = fills?.origin_pct ?? (total > 0 ? Math.round(100 * (stats.products_with_origin ?? 0) / total) : 0);
  const processPct = fills?.process_pct ?? (total > 0 ? Math.round(100 * (stats.products_with_process ?? 0) / total) : 0);
  const roastPct = fills?.roast_pct ?? (total > 0 ? Math.round(100 * (stats.products_with_roast_level ?? 0) / total) : 0);
  const varietyPct = fills?.variety_pct ?? 0;

  const avgPct = Math.round((originPct + processPct + roastPct + varietyPct) / 4);

  return (
    <div className="rounded-lg border bg-card px-4 py-4">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <p className="text-sm font-semibold text-foreground">📊 Coffee Metadata Quality</p>
          <p className="text-xs text-muted-foreground mt-0.5">{total} products · avg {avgPct}% filled</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <PctBadge label="Origin" pct={originPct} />
          <PctBadge label="Process" pct={processPct} />
          <PctBadge label="Roast" pct={roastPct} />
          <PctBadge label="Variety" pct={varietyPct} />
        </div>
      </div>
    </div>
  );
}
