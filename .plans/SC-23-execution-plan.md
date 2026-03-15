# SC-23 Execution Plan: Merchant Detail Page

## Route: `frontend/src/routes/merchants.$id.tsx`
```tsx
import { createFileRoute } from "@tanstack/react-router";
import { useMerchant } from "@/hooks/useMerchant";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MerchantInfoCard } from "@/components/merchants/MerchantInfoCard";
import { ProductsTab } from "@/components/merchants/ProductsTab";
import { CrawlRunsTab } from "@/components/merchants/CrawlRunsTab";
import { PromosTab } from "@/components/merchants/PromosTab";

export const Route = createFileRoute("/merchants/$id")({
  component: MerchantDetailPage,
});

function MerchantDetailPage() {
  const { id } = Route.useParams();
  const { data: merchant, isLoading } = useMerchant(Number(id));

  if (isLoading) return <div className="p-6">Loading...</div>;
  if (!merchant) return <div className="p-6">Merchant not found</div>;

  return (
    <div className="space-y-6">
      <MerchantInfoCard merchant={merchant} />
      <Tabs defaultValue="products">
        <TabsList>
          <TabsTrigger value="products">Products</TabsTrigger>
          <TabsTrigger value="crawls">Crawl Runs</TabsTrigger>
          <TabsTrigger value="promos">Promos</TabsTrigger>
        </TabsList>
        <TabsContent value="products"><ProductsTab merchantId={Number(id)} /></TabsContent>
        <TabsContent value="crawls"><CrawlRunsTab merchantId={Number(id)} /></TabsContent>
        <TabsContent value="promos"><PromosTab merchantId={Number(id)} /></TabsContent>
      </Tabs>
    </div>
  );
}
```

## `frontend/src/hooks/useMerchant.ts`
```typescript
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";

export function useMerchant(id: number) {
  return useQuery({
    queryKey: ["merchants", id],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/merchants/{merchant_id}", {
        params: { path: { merchant_id: id } },
      });
      if (error) throw error;
      return data;
    },
    enabled: !!id,
  });
}
```

## `frontend/src/components/merchants/MerchantInfoCard.tsx`
```tsx
import type { MerchantDetail } from "@/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrustBadge } from "@/components/ui/trust-badge";
import { QualityScores } from "./QualityScores";

export function MerchantInfoCard({ merchant }: { merchant: MerchantDetail }) {
  const latestShipping = merchant.shipping_policies?.[0];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl">{merchant.name}</CardTitle>
          <TrustBadge tier={merchant.trust_tier as any} />
        </div>
        <a href={merchant.homepage_url} target="_blank" rel="noreferrer"
           className="text-sm text-blue-600 hover:underline">{merchant.canonical_domain}</a>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm text-muted-foreground">Platform</p>
          <p className="capitalize font-medium">{merchant.platform_type}</p>
        </div>
        <div>
          <p className="text-sm text-muted-foreground">Country</p>
          <p className="font-medium">{merchant.country_code}</p>
        </div>
        {latestShipping?.free_shipping_threshold_cents && (
          <div>
            <p className="text-sm text-muted-foreground">Free Shipping Over</p>
            <p className="font-medium">${(latestShipping.free_shipping_threshold_cents / 100).toFixed(0)}</p>
          </div>
        )}
        {merchant.quality_profile && (
          <div className="col-span-2">
            <p className="text-sm text-muted-foreground mb-2">Quality Scores</p>
            <QualityScores profile={merchant.quality_profile} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

## `frontend/src/components/merchants/QualityScores.tsx`
```tsx
// Render quality_profile scores as labeled progress bars
// Fields: freshness_transparency_score, shipping_clarity_score, metadata_quality_score,
//         espresso_relevance_score, service_confidence_score, overall_quality_score
// Each 0.0-1.0 → render as colored progress bar (green >0.7, amber 0.4-0.7, red <0.4)
```

## `frontend/src/components/merchants/ProductsTab.tsx`
```tsx
// useMerchantProducts hook → GET /api/v1/merchants/{id}/products
// Table: product name, variant count, min price, espresso badge, link to product detail
// Show origin_text if non-empty (currently mostly empty)
```

## `frontend/src/components/merchants/CrawlRunsTab.tsx`
```tsx
// useCrawlRuns hook → GET /api/v1/merchants/{id}/crawl-runs
// Table: started_at, status badge, adapter_name, records_written, duration_seconds
```

## `frontend/src/components/merchants/PromosTab.tsx`
```tsx
// useQuery → GET /api/v1/merchants/{id} (promos via separate promos endpoint or included)
// Cards: promo_type, title, code (copyable), estimated_value_dollars, is_active badge
```
