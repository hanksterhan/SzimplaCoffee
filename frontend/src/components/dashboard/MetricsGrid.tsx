import type { DashboardMetrics } from "@/hooks/use-dashboard";
import { StatsCard } from "./StatsCard";

interface MetricsGridProps {
  stats?: DashboardMetrics;
  loading: boolean;
}

export function MetricsGrid({ stats, loading }: MetricsGridProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      <StatsCard
        title="Merchants"
        value={stats?.merchant_count ?? 0}
        icon="🏪"
        loading={loading}
      />
      <StatsCard
        title="Products"
        value={stats?.product_count ?? 0}
        icon="📦"
        loading={loading}
      />
      <StatsCard
        title="Variants"
        value={stats?.variant_count ?? 0}
        icon="🔢"
        loading={loading}
      />
      <StatsCard
        title="Offers"
        value={stats?.offer_count ?? 0}
        icon="💰"
        loading={loading}
      />
      <StatsCard
        title="Crawl Runs"
        value={stats?.crawl_run_count ?? 0}
        subtitle={stats?.last_crawl_at ? `Last: ${new Date(stats.last_crawl_at).toLocaleDateString()}` : undefined}
        icon="🕷️"
        loading={loading}
      />
      <StatsCard
        title="Recommendations"
        value={stats?.recommendation_count ?? 0}
        icon="🎯"
        loading={loading}
      />
    </div>
  );
}
