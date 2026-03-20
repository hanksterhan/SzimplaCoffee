import type { components } from "@/api/schema";
import type { DashboardMetrics } from "@/hooks/use-dashboard";
import { MetadataFillRateWidget } from "@/components/MetadataFillRateWidget";

interface MetadataFillRateProps {
  stats?: DashboardMetrics;
  loading: boolean;
}

type MetadataFillRates = components["schemas"]["MetadataFillRates"];

export function MetadataFillRate({ stats, loading }: MetadataFillRateProps) {
  if (loading || !stats) {
    return (
      <div className="rounded-lg border bg-card px-4 py-4">
        <p className="text-sm font-semibold text-foreground mb-3">📊 Coffee Metadata Quality</p>
        <MetadataFillRateWidget fillRates={undefined} />
      </div>
    );
  }

  const total = stats.total_products ?? 0;
  const fills: MetadataFillRates | undefined = stats.metadata_fill_rates;

  // Build a normalized MetadataFillRates shape, falling back to raw counts if needed
  const fillRates: MetadataFillRates = fills ?? {
    origin_pct: total > 0 ? Math.round((100 * (stats.products_with_origin ?? 0)) / total) : 0,
    process_pct: total > 0 ? Math.round((100 * (stats.products_with_process ?? 0)) / total) : 0,
    roast_pct: total > 0 ? Math.round((100 * (stats.products_with_roast_level ?? 0)) / total) : 0,
    variety_pct: 0,
    coffee_product_count: total,
  };

  const avgPct = Math.round(
    (fillRates.origin_pct + fillRates.process_pct + fillRates.roast_pct + fillRates.variety_pct) / 4
  );

  return (
    <div className="rounded-lg border bg-card px-4 py-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <p className="text-sm font-semibold text-foreground">📊 Coffee Metadata Quality</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            {total} products · avg {avgPct}% filled
          </p>
        </div>
      </div>
      <MetadataFillRateWidget fillRates={fillRates} />
    </div>
  );
}
