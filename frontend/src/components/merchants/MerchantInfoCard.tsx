import type { components } from "@/api/schema";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrustBadge } from "@/components/ui/trust-badge";
import { CrawlTierBadge } from "./CrawlTierBadge";
import { QualityScores } from "./QualityScores";
import { Button } from "@/components/ui/button";
import { useTriggerCrawl } from "@/hooks/use-merchants";

type MerchantDetail = components["schemas"]["MerchantDetail"];

interface MerchantInfoCardProps {
  merchant: MerchantDetail;
}

export function MerchantInfoCard({ merchant }: MerchantInfoCardProps) {
  const triggerCrawl = useTriggerCrawl();
  const latestShipping = merchant.shipping_policies?.[0];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <CardTitle className="text-xl">{merchant.name}</CardTitle>
            <a
              href={merchant.homepage_url}
              target="_blank"
              rel="noreferrer"
              className="text-sm text-blue-600 hover:underline"
            >
              {merchant.canonical_domain} ↗
            </a>
          </div>
          <div className="flex items-center gap-2 flex-wrap justify-end">
            <CrawlTierBadge tier={merchant.crawl_tier} />
            <TrustBadge
              tier={
                merchant.trust_tier as
                  | "trusted"
                  | "verified"
                  | "candidate"
                  | "rejected"
              }
            />
            <Button
              size="sm"
              variant="outline"
              onClick={() => triggerCrawl.mutate({ merchantId: merchant.id, merchantName: merchant.name })}
              disabled={triggerCrawl.isPending}
            >
              {triggerCrawl.isPending ? "Crawling…" : "🕷️ Trigger Crawl"}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <p className="text-xs text-muted-foreground">Platform</p>
          <p className="capitalize font-medium">{merchant.platform_type}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Country</p>
          <p className="font-medium">{merchant.country_code}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Status</p>
          <p className={`font-medium ${merchant.is_active ? "text-green-600" : "text-gray-400"}`}>
            {merchant.is_active ? "Active" : "Inactive"}
          </p>
        </div>
        {latestShipping?.free_shipping_threshold_cents ? (
          <div>
            <p className="text-xs text-muted-foreground">Free Shipping Over</p>
            <p className="font-medium">
              ${(latestShipping.free_shipping_threshold_cents / 100).toFixed(0)}
            </p>
          </div>
        ) : (
          <div>
            <p className="text-xs text-muted-foreground">Free Shipping</p>
            <p className="text-muted-foreground text-sm">—</p>
          </div>
        )}
        {merchant.quality_profile && (
          <div className="col-span-2 md:col-span-4">
            <p className="text-xs text-muted-foreground mb-3">Quality Scores</p>
            <QualityScores profile={merchant.quality_profile} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
