import { createLazyFileRoute, Link } from "@tanstack/react-router";
import { useMerchant } from "@/hooks/use-merchants";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MerchantInfoCard } from "@/components/merchants/MerchantInfoCard";
import { ProductsTab } from "@/components/merchants/ProductsTab";
import { CrawlRunsTab } from "@/components/merchants/CrawlRunsTab";
import { PromosTab } from "@/components/merchants/PromosTab";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";

export const Route = createLazyFileRoute("/merchants/$merchantId")({
  component: MerchantDetailPage,
});

function MerchantDetailPage() {
  const { merchantId } = Route.useParams();
  const id = Number(merchantId);
  const { data: merchant, isLoading, error } = useMerchant(id);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (error || !merchant) {
    return (
      <div className="py-16 text-center space-y-4">
        <p className="text-muted-foreground text-lg">Merchant not found.</p>
        <Link to="/merchants">
          <Button variant="outline">← Back to Merchants</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link to="/merchants" className="hover:underline">
          Merchants
        </Link>
        <span>/</span>
        <span className="text-foreground font-medium">{merchant.name}</span>
      </div>

      <MerchantInfoCard merchant={merchant} />

      <Tabs defaultValue="products">
        <TabsList>
          <TabsTrigger value="products">📦 Products</TabsTrigger>
          <TabsTrigger value="crawls">🕷️ Crawl Runs</TabsTrigger>
          <TabsTrigger value="promos">🎁 Promos</TabsTrigger>
        </TabsList>
        <TabsContent value="products">
          <ProductsTab merchantId={id} />
        </TabsContent>
        <TabsContent value="crawls">
          <CrawlRunsTab merchantId={id} />
        </TabsContent>
        <TabsContent value="promos">
          <PromosTab merchantId={id} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
