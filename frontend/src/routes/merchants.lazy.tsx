import { createLazyFileRoute, useNavigate, Link } from "@tanstack/react-router";
import { useState } from "react";
import { useMerchants, useTriggerCrawl } from "@/hooks/use-merchants";
import { TrustBadge } from "@/components/ui/trust-badge";
import { CrawlTierBadge } from "@/components/merchants/CrawlTierBadge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";

export const Route = createLazyFileRoute("/merchants")({
  component: MerchantsPage,
});

function MerchantsPage() {
  const navigate = useNavigate({ from: "/merchants" });
  const search = Route.useSearch();
  const platformType = search.platform_type ?? "";
  const [platformOpen, setPlatformOpen] = useState(false);
  const [trustOpen, setTrustOpen] = useState(false);
  const trustTier = search.trust_tier ?? "";

  const { data, isLoading } = useMerchants({
    platform_type: platformType || undefined,
    trust_tier: trustTier || undefined,
    page_size: 50,
  });

  const triggerCrawl = useTriggerCrawl();

  const setFilter = (key: "platform_type" | "trust_tier", value: string) => {
    navigate({
      search: (prev) => ({
        ...prev,
        [key]: value || undefined,
      }),
    });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">🏪 Merchants</h1>
          <p className="text-muted-foreground text-sm">
            {data?.total ?? 0} merchants
          </p>
        </div>
        <Link to="/merchants/new">
          <Button>+ Add Merchant</Button>
        </Link>
      </div>

      {/* Filter bar */}
      <div className="flex gap-3 flex-wrap">
        <Select
          value={platformType || "_all"}
          onValueChange={(v) => setFilter("platform_type", v === "_all" ? "" : v)}
          open={platformOpen}
          onOpenChange={setPlatformOpen}
        >
          <SelectTrigger className="w-44" onClick={() => setPlatformOpen((v) => !v)}>
            <SelectValue placeholder="All Platforms" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="_all">All Platforms</SelectItem>
            <SelectItem value="shopify">Shopify</SelectItem>
            <SelectItem value="woocommerce">WooCommerce</SelectItem>
            <SelectItem value="agentic">Agentic</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={trustTier || "_all"}
          onValueChange={(v) => setFilter("trust_tier", v === "_all" ? "" : v)}
          open={trustOpen}
          onOpenChange={setTrustOpen}
        >
          <SelectTrigger className="w-40" onClick={() => setTrustOpen((v) => !v)}>
            <SelectValue placeholder="All Trust" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="_all">All Trust</SelectItem>
            <SelectItem value="trusted">Trusted</SelectItem>
            <SelectItem value="verified">Verified</SelectItem>
            <SelectItem value="candidate">Candidate</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Domain</TableHead>
              <TableHead>Platform</TableHead>
              <TableHead>Tier</TableHead>
              <TableHead>Trust</TableHead>
              <TableHead>Country</TableHead>
              <TableHead>Active</TableHead>
              <TableHead></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.items.map((m) => (
              <TableRow
                key={m.id}
                className="cursor-pointer hover:bg-muted/50"
                onClick={() =>
                  navigate({
                    to: "/merchants/$merchantId",
                    params: { merchantId: String(m.id) },
                  })
                }
              >
                <TableCell className="font-medium">{m.name}</TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {m.canonical_domain}
                </TableCell>
                <TableCell className="capitalize text-sm">
                  {m.platform_type}
                </TableCell>
                <TableCell>
                  <CrawlTierBadge tier={m.crawl_tier} />
                </TableCell>
                <TableCell>
                  <TrustBadge
                    tier={
                      m.trust_tier as
                        | "trusted"
                        | "verified"
                        | "candidate"
                        | "rejected"
                    }
                  />
                </TableCell>
                <TableCell className="text-sm">{m.country_code}</TableCell>
                <TableCell>
                  <span
                    className={`text-sm font-medium ${m.is_active ? "text-green-600" : "text-gray-400"}`}
                  >
                    {m.is_active ? "✓" : "—"}
                  </span>
                </TableCell>
                <TableCell>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={(e) => {
                      e.stopPropagation();
                      triggerCrawl.mutate({ merchantId: m.id, merchantName: m.name });
                    }}
                    disabled={triggerCrawl.isPending}
                  >
                    Crawl
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
