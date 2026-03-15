import { createLazyFileRoute, Link } from "@tanstack/react-router";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  useWatchlist,
  useRemoveFromWatchlist,
  useLowConfidenceMerchants,
  type MerchantSummary,
} from "@/hooks/use-watchlist";
import { toast } from "sonner";

export const Route = createLazyFileRoute("/watch")({
  component: WatchPage,
});

function TrustBadge({ tier }: { tier: string }) {
  const colors: Record<string, string> = {
    trusted: "bg-green-100 text-green-800 border-green-300",
    verified: "bg-blue-100 text-blue-800 border-blue-300",
    candidate: "bg-yellow-100 text-yellow-800 border-yellow-300",
    rejected: "bg-red-100 text-red-800 border-red-300",
  };
  return (
    <Badge
      variant="outline"
      className={`text-xs ${colors[tier] ?? "bg-gray-100 text-gray-700"}`}
    >
      {tier}
    </Badge>
  );
}

function MerchantRow({
  merchant,
  action,
}: {
  merchant: MerchantSummary;
  action: React.ReactNode;
}) {
  return (
    <div className="flex items-center gap-3 py-2 border-b last:border-0">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <Link
            to="/merchants/$merchantId"
            params={{ merchantId: String(merchant.id) }}
            className="font-medium text-sm hover:underline"
          >
            {merchant.name}
          </Link>
          <TrustBadge tier={merchant.trust_tier} />
          <Badge variant="outline" className="text-xs">
            Tier {merchant.crawl_tier}
          </Badge>
        </div>
        <p className="text-xs text-muted-foreground mt-0.5">
          {merchant.canonical_domain} · {merchant.platform_type}
        </p>
      </div>
      {action}
    </div>
  );
}

function WatchlistTab() {
  const { data: watched, isLoading } = useWatchlist();
  const { mutate: remove } = useRemoveFromWatchlist();

  if (isLoading) {
    return (
      <div className="space-y-2 mt-4">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (!watched || watched.length === 0) {
    return (
      <div className="mt-6 text-center text-muted-foreground py-8">
        <p className="text-3xl mb-2">👁️</p>
        <p className="font-medium">No merchants on watchlist</p>
        <p className="text-sm mt-1">
          Add merchants from the{" "}
          <Link to="/merchants" className="underline">
            Merchants
          </Link>{" "}
          page.
        </p>
      </div>
    );
  }

  return (
    <div className="mt-4">
      {watched.map((m) => (
        <MerchantRow
          key={m.id}
          merchant={m}
          action={
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-red-600 hover:text-red-700"
              onClick={() => {
                remove(m.id);
                toast.success(`Removed ${m.name} from watchlist`);
              }}
            >
              Remove
            </Button>
          }
        />
      ))}
    </div>
  );
}

function ReviewQueueTab() {
  const { data: lowConf, isLoading } = useLowConfidenceMerchants(0.5);

  if (isLoading) {
    return (
      <div className="space-y-2 mt-4">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (!lowConf || lowConf.length === 0) {
    return (
      <div className="mt-6 text-center text-muted-foreground py-8">
        <p className="text-3xl mb-2">✅</p>
        <p className="font-medium">All merchants have good crawl quality</p>
        <p className="text-sm mt-1">No merchants need attention.</p>
      </div>
    );
  }

  return (
    <div className="mt-4">
      <p className="text-sm text-muted-foreground mb-3">
        {lowConf.length} merchant{lowConf.length === 1 ? "" : "s"} with low crawl quality — review
        and re-crawl or adjust tier.
      </p>
      {lowConf.map((m) => (
        <MerchantRow
          key={m.id}
          merchant={m}
          action={
            <div className="flex gap-1 shrink-0">
              <Link
                to="/merchants/$merchantId"
                params={{ merchantId: String(m.id) }}
              >
                <Button variant="outline" size="sm" className="text-xs">
                  Review →
                </Button>
              </Link>
            </div>
          }
        />
      ))}
    </div>
  );
}

function WatchPage() {
  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold">👁️ Watch &amp; Review</h1>
        <p className="text-muted-foreground">
          Watched merchants and low-confidence crawl queue
        </p>
      </div>

      <Tabs defaultValue="watchlist">
        <TabsList>
          <TabsTrigger value="watchlist">Watchlist</TabsTrigger>
          <TabsTrigger value="review">Review Queue</TabsTrigger>
        </TabsList>

        <TabsContent value="watchlist">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Watched Merchants</CardTitle>
            </CardHeader>
            <CardContent>
              <WatchlistTab />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="review">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Low-Confidence Crawl Queue</CardTitle>
            </CardHeader>
            <CardContent>
              <ReviewQueueTab />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
