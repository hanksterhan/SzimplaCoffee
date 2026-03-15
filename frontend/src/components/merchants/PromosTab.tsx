import { useMerchantPromos } from "@/hooks/use-merchants";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent } from "@/components/ui/card";
import { useState } from "react";

interface PromosTabProps {
  merchantId: number;
}

export function PromosTab({ merchantId }: PromosTabProps) {
  const { data, isLoading } = useMerchantPromos(merchantId);
  const [copied, setCopied] = useState<string | null>(null);

  const copyCode = (code: string) => {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(code);
      setTimeout(() => setCopied(null), 2000);
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-3 mt-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-24 w-full" />
        ))}
      </div>
    );
  }

  if (!data?.length) {
    return (
      <div className="py-12 text-center text-muted-foreground">
        No promotions found.
      </div>
    );
  }

  const active = data.filter((p) => p.is_active);
  const inactive = data.filter((p) => !p.is_active);

  return (
    <div className="mt-4 space-y-6">
      {active.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-muted-foreground mb-3">
            Active Promos ({active.length})
          </h3>
          <div className="grid gap-3 md:grid-cols-2">
            {active.map((promo) => (
              <PromoCard
                key={promo.id}
                promo={promo}
                copied={copied}
                onCopy={copyCode}
              />
            ))}
          </div>
        </div>
      )}
      {inactive.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-muted-foreground mb-3">
            Past Promos ({inactive.length})
          </h3>
          <div className="grid gap-3 md:grid-cols-2 opacity-60">
            {inactive.map((promo) => (
              <PromoCard
                key={promo.id}
                promo={promo}
                copied={copied}
                onCopy={copyCode}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

interface PromoCardProps {
  promo: {
    id: number;
    promo_type: string;
    title: string;
    details: string;
    code: string | null;
    estimated_value_dollars: number | null;
    confidence: number;
    is_active: boolean;
  };
  copied: string | null;
  onCopy: (code: string) => void;
}

function PromoCard({ promo, copied, onCopy }: PromoCardProps) {
  return (
    <Card className="text-sm">
      <CardContent className="p-4 space-y-2">
        <div className="flex items-start justify-between gap-2">
          <span className="font-medium">{promo.title}</span>
          <Badge
            variant="outline"
            className={`text-xs shrink-0 ${promo.is_active ? "bg-green-50 text-green-700 border-green-200" : "bg-gray-50 text-gray-500"}`}
          >
            {promo.is_active ? "Active" : "Expired"}
          </Badge>
        </div>
        <p className="text-muted-foreground text-xs">{promo.details}</p>
        <div className="flex items-center gap-3 flex-wrap">
          <Badge variant="secondary" className="text-xs">
            {promo.promo_type}
          </Badge>
          {promo.estimated_value_dollars !== null && (
            <span className="text-xs text-green-700 font-medium">
              ~${promo.estimated_value_dollars.toFixed(2)} value
            </span>
          )}
          <span className="text-xs text-muted-foreground">
            {Math.round(promo.confidence * 100)}% confidence
          </span>
        </div>
        {promo.code && (
          <button
            onClick={() => onCopy(promo.code!)}
            className="inline-flex items-center gap-2 px-2 py-1 bg-muted rounded text-xs font-mono hover:bg-muted/80 transition-colors"
          >
            <span>{promo.code}</span>
            <span className="text-muted-foreground">
              {copied === promo.code ? "✓ Copied!" : "📋"}
            </span>
          </button>
        )}
      </CardContent>
    </Card>
  );
}
