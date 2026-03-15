# SC-22 Execution Plan: Merchant List Page

## `frontend/src/hooks/useMerchants.ts`
```typescript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";

interface MerchantsFilter {
  platform_type?: string;
  trust_tier?: string;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}

export function useMerchants(filters: MerchantsFilter = {}) {
  return useQuery({
    queryKey: ["merchants", filters],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/merchants", {
        params: {
          query: {
            platform_type: filters.platform_type,
            trust_tier: filters.trust_tier,
            is_active: filters.is_active,
            page: filters.page ?? 1,
            page_size: filters.page_size ?? 25,
          },
        },
      });
      if (error) throw error;
      return data;
    },
    staleTime: 30_000,
  });
}
```

## `frontend/src/hooks/useTriggerCrawl.ts`
```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";

export function useTriggerCrawl() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (merchantId: number) => {
      const { data, error } = await api.POST("/api/v1/merchants/{merchant_id}/crawl", {
        params: { path: { merchant_id: merchantId } },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["merchants"] });
    },
  });
}
```

## `frontend/src/components/merchants/CrawlStatusBadge.tsx`
```tsx
import { Badge } from "@/components/ui/badge";

const STATUS_CONFIG = {
  completed: { label: "Crawled", className: "bg-green-100 text-green-700" },
  failed: { label: "Failed", className: "bg-red-100 text-red-700" },
  started: { label: "Running...", className: "bg-blue-100 text-blue-700" },
  never: { label: "Never", className: "bg-gray-100 text-gray-500" },
} as const;

type CrawlStatus = keyof typeof STATUS_CONFIG;

export function CrawlStatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status as CrawlStatus] ?? STATUS_CONFIG.never;
  return <Badge variant="outline" className={`text-xs ${cfg.className}`}>{cfg.label}</Badge>;
}
```

## `frontend/src/components/merchants/MerchantFilters.tsx`
```tsx
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface MerchantFiltersProps {
  platformType: string;
  trustTier: string;
  onPlatformChange: (v: string) => void;
  onTrustChange: (v: string) => void;
}

export function MerchantFilters({ platformType, trustTier, onPlatformChange, onTrustChange }: MerchantFiltersProps) {
  return (
    <div className="flex gap-3">
      <Select value={platformType} onValueChange={onPlatformChange}>
        <SelectTrigger className="w-40">
          <SelectValue placeholder="All Platforms" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="">All Platforms</SelectItem>
          <SelectItem value="shopify">Shopify (14)</SelectItem>
          <SelectItem value="woocommerce">WooCommerce (1)</SelectItem>
          <SelectItem value="agentic">Agentic (1)</SelectItem>
        </SelectContent>
      </Select>

      <Select value={trustTier} onValueChange={onTrustChange}>
        <SelectTrigger className="w-36">
          <SelectValue placeholder="All Trust" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="">All Trust</SelectItem>
          <SelectItem value="trusted">Trusted</SelectItem>
          <SelectItem value="verified">Verified</SelectItem>
          <SelectItem value="candidate">Candidate</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
```

## `frontend/src/routes/merchants.tsx` (list)
```tsx
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { useMerchants } from "@/hooks/useMerchants";
import { useTriggerCrawl } from "@/hooks/useTriggerCrawl";
import { MerchantFilters } from "@/components/merchants/MerchantFilters";
import { TrustBadge } from "@/components/ui/trust-badge";
import { CrawlStatusBadge } from "@/components/merchants/CrawlStatusBadge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Link } from "@tanstack/react-router";

export const Route = createFileRoute("/merchants")({
  component: MerchantsPage,
});

function MerchantsPage() {
  const [platformType, setPlatformType] = useState("");
  const [trustTier, setTrustTier] = useState("");
  const { data, isLoading } = useMerchants({ platform_type: platformType || undefined, trust_tier: trustTier || undefined });
  const triggerCrawl = useTriggerCrawl();

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">🏪 Merchants</h1>
        <Link to="/merchants/new"><Button>+ Add Merchant</Button></Link>
      </div>
      <MerchantFilters
        platformType={platformType}
        trustTier={trustTier}
        onPlatformChange={setPlatformType}
        onTrustChange={setTrustTier}
      />
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Platform</TableHead>
            <TableHead>Trust</TableHead>
            <TableHead>Domain</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data?.items.map((m) => (
            <TableRow key={m.id} className="cursor-pointer hover:bg-muted/50">
              <TableCell>
                <Link to="/merchants/$id" params={{ id: String(m.id) }} className="font-medium hover:underline">
                  {m.name}
                </Link>
              </TableCell>
              <TableCell className="capitalize">{m.platform_type}</TableCell>
              <TableCell><TrustBadge tier={m.trust_tier as any} /></TableCell>
              <TableCell className="text-sm text-muted-foreground">{m.canonical_domain}</TableCell>
              <TableCell>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => triggerCrawl.mutate(m.id)}
                  disabled={triggerCrawl.isPending}
                >
                  Crawl
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <p className="text-sm text-muted-foreground">{data?.total ?? 0} merchants</p>
    </div>
  );
}
```
