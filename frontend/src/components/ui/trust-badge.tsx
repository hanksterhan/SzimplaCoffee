import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type TrustTier = "trusted" | "verified" | "candidate" | "rejected";

const tierConfig: Record<TrustTier, { label: string; className: string }> = {
  trusted: { label: "Trusted", className: "bg-green-100 text-green-800 border-green-200" },
  verified: { label: "Verified", className: "bg-blue-100 text-blue-800 border-blue-200" },
  candidate: { label: "Candidate", className: "bg-amber-100 text-amber-800 border-amber-200" },
  rejected: { label: "Rejected", className: "bg-red-100 text-red-800 border-red-200" },
};

export function TrustBadge({ tier }: { tier: TrustTier }) {
  const { label, className } = tierConfig[tier] ?? tierConfig.candidate;
  return (
    <Badge variant="outline" className={cn("text-xs", className)}>
      {label}
    </Badge>
  );
}
