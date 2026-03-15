import { Badge } from "@/components/ui/badge";

const TIER_CONFIG: Record<string, { className: string }> = {
  A: { className: "bg-green-100 text-green-800 border-green-200" },
  B: { className: "bg-blue-100 text-blue-800 border-blue-200" },
  C: { className: "bg-gray-100 text-gray-700 border-gray-200" },
  D: { className: "bg-orange-100 text-orange-800 border-orange-200" },
};

export function CrawlTierBadge({ tier }: { tier: string }) {
  const cfg = TIER_CONFIG[tier?.toUpperCase()] ?? TIER_CONFIG["C"];
  return (
    <Badge variant="outline" className={`text-xs font-mono ${cfg.className}`}>
      {tier?.toUpperCase() ?? "?"}
    </Badge>
  );
}
