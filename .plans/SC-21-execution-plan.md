# SC-21 Execution Plan: Dashboard Page

## `frontend/src/hooks/useDashboard.ts`
```typescript
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import type { DashboardStats } from "@/api";

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/dashboard");
      if (error) throw error;
      return data as DashboardStats;
    },
    staleTime: 30_000,
    refetchInterval: 30_000,
  });
}
```

## `frontend/src/components/dashboard/StatsCard.tsx`
```tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface StatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: string;
  loading?: boolean;
}

export function StatsCard({ title, value, subtitle, icon, loading }: StatsCardProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <Skeleton className="h-4 w-24" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-16" />
          <Skeleton className="h-3 w-32 mt-1" />
        </CardContent>
      </Card>
    );
  }
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          {icon && <span>{icon}</span>}
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-bold">{value}</p>
        {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
      </CardContent>
    </Card>
  );
}
```

## `frontend/src/components/dashboard/MetricsGrid.tsx`
```tsx
import type { DashboardStats } from "@/api";
import { StatsCard } from "./StatsCard";

interface MetricsGridProps {
  stats?: DashboardStats;
  loading: boolean;
}

export function MetricsGrid({ stats, loading }: MetricsGridProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <StatsCard
        title="Merchants"
        value={stats?.merchants.total ?? 0}
        subtitle={`${stats?.merchants.trusted_count ?? 0} trusted`}
        icon="🏪"
        loading={loading}
      />
      <StatsCard
        title="Products"
        value={stats?.products.active ?? 0}
        subtitle={`${stats?.products.espresso_recommended ?? 0} espresso picks`}
        icon="📦"
        loading={loading}
      />
      <StatsCard
        title="Variants"
        value={stats?.products.variants_total ?? 0}
        icon="🔢"
        loading={loading}
      />
      <StatsCard
        title="Avg Price"
        value={stats ? `$${((stats.offers.avg_price_cents ?? 0) / 100).toFixed(2)}` : "--"}
        subtitle={`Range: $${((stats?.offers.min_price_cents ?? 0) / 100).toFixed(0)} – $${((stats?.offers.max_price_cents ?? 0) / 100).toFixed(0)}`}
        icon="💰"
        loading={loading}
      />
    </div>
  );
}
```

## `frontend/src/routes/index.tsx`
```tsx
import { createFileRoute } from "@tanstack/react-router";
import { useDashboard } from "@/hooks/useDashboard";
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
```

## `frontend/src/components/dashboard/MerchantOverviewTable.tsx`
```tsx
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { TrustBadge } from "@/components/ui/trust-badge";

export function MerchantOverviewTable() {
  const { data } = useQuery({
    queryKey: ["merchants", "overview"],
    queryFn: async () => {
      const { data } = await api.GET("/api/v1/merchants", { params: { query: { page_size: 20 } } });
      return data;
    },
  });

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Merchant</TableHead>
          <TableHead>Platform</TableHead>
          <TableHead>Trust</TableHead>
          <TableHead>Domain</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data?.items.map((m) => (
          <TableRow key={m.id} className={m.is_trusted ? "bg-green-50/30" : ""}>
            <TableCell className="font-medium">{m.name}</TableCell>
            <TableCell className="capitalize">{m.platform_type}</TableCell>
            <TableCell><TrustBadge tier={m.trust_tier as any} /></TableCell>
            <TableCell className="text-muted-foreground text-sm">{m.canonical_domain}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
```
