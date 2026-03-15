import { useMerchants } from "@/hooks/use-merchants";
import { Link } from "@tanstack/react-router";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { TrustBadge } from "@/components/ui/trust-badge";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

const TIER_CONFIG: Record<string, { className: string }> = {
  A: { className: "bg-green-100 text-green-800 border-green-200" },
  B: { className: "bg-blue-100 text-blue-800 border-blue-200" },
  C: { className: "bg-gray-100 text-gray-700 border-gray-200" },
  D: { className: "bg-orange-100 text-orange-800 border-orange-200" },
};

function CrawlTierBadge({ tier }: { tier: string }) {
  const cfg = TIER_CONFIG[tier?.toUpperCase()] ?? TIER_CONFIG["C"];
  return (
    <Badge variant="outline" className={`text-xs font-mono ${cfg.className}`}>
      {tier}
    </Badge>
  );
}

export function MerchantOverviewTable() {
  const { data, isLoading } = useMerchants({ page_size: 20 });

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-lg font-semibold mb-3">Merchant Overview</h2>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Platform</TableHead>
            <TableHead>Tier</TableHead>
            <TableHead>Trust</TableHead>
            <TableHead>Country</TableHead>
            <TableHead>Active</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data?.items.map((m) => (
            <TableRow key={m.id} className="hover:bg-muted/50">
              <TableCell className="font-medium">
                <Link
                  to="/merchants/$merchantId"
                  params={{ merchantId: String(m.id) }}
                  className="hover:underline text-blue-600"
                >
                  {m.name}
                </Link>
              </TableCell>
              <TableCell className="capitalize text-sm">{m.platform_type}</TableCell>
              <TableCell>
                <CrawlTierBadge tier={m.crawl_tier} />
              </TableCell>
              <TableCell>
                <TrustBadge tier={m.trust_tier as "trusted" | "verified" | "candidate" | "rejected"} />
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">{m.country_code}</TableCell>
              <TableCell>
                <span className={`text-sm font-medium ${m.is_active ? "text-green-600" : "text-gray-400"}`}>
                  {m.is_active ? "✓" : "—"}
                </span>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <p className="text-sm text-muted-foreground mt-2">{data?.total ?? 0} total merchants</p>
    </div>
  );
}
