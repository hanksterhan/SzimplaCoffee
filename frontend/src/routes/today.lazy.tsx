import { createLazyFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useTodayBrief, type TodayBriefResult } from "@/hooks/use-today";

export const Route = createLazyFileRoute("/today")({
  component: TodayPage,
});

function fmtPrice(cents: number) {
  return `$${(cents / 100).toFixed(2)}`;
}

function fmtPricePerOz(cents: number | null | undefined) {
  if (!cents) return null;
  return `$${(cents / 100).toFixed(2)}/oz`;
}

function TopPickCard({
  pick,
}: {
  pick: NonNullable<TodayBriefResult["top_pick"]>;
}) {
  const perOz = fmtPricePerOz(pick.landed_price_per_oz_cents);
  const discounted = pick.discounted_landed_price_cents;
  return (
    <Card className="border-2 border-amber-700 shadow-md bg-amber-50/40">
      <div className="px-4 pt-3 pb-0">
        <Badge className="bg-amber-700 text-white text-xs">
          ⭐ Today&apos;s Top Pick
        </Badge>
      </div>
      <CardHeader className="pb-2">
        <div className="flex gap-4">
          {pick.image_url ? (
            <img
              src={pick.image_url}
              alt={pick.product_name}
              className="w-16 h-16 object-cover rounded-md border shrink-0"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = "none";
              }}
            />
          ) : (
            <div className="w-16 h-16 rounded-md border bg-amber-100 flex items-center justify-center shrink-0">
              <span className="text-2xl">☕</span>
            </div>
          )}
          <div className="flex-1 min-w-0">
            <CardTitle className="text-base leading-tight line-clamp-2">
              {pick.product_name}
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-0.5">
              {pick.merchant_name} · {pick.variant_label}
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex items-baseline gap-2">
          {discounted ? (
            <>
              <span className="text-xl font-bold text-amber-800">
                {fmtPrice(discounted)}
              </span>
              <span className="text-sm line-through text-muted-foreground">
                {fmtPrice(pick.landed_price_cents)}
              </span>
            </>
          ) : (
            <span className="text-xl font-bold">{fmtPrice(pick.landed_price_cents)}</span>
          )}
          {perOz && (
            <span className="text-xs text-muted-foreground">({perOz})</span>
          )}
        </div>
        {pick.pros.length > 0 && (
          <ul className="text-sm text-muted-foreground space-y-1">
            {pick.pros.map((pro, i) => (
              <li key={i}>✓ {pro}</li>
            ))}
          </ul>
        )}
        <a
          href={pick.product_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block mt-2"
        >
          <Button size="sm" className="bg-amber-700 hover:bg-amber-800 text-white">
            View &amp; Buy →
          </Button>
        </a>
      </CardContent>
    </Card>
  );
}

function SaleCard({
  sale,
}: {
  sale: NonNullable<TodayBriefResult["notable_sales"]>[number];
}) {
  const dropped7d = sale.price_drop_7d_percent;
  const dropped30d = sale.price_drop_30d_percent;
  const badge =
    sale.compare_at_discount_percent > 0
      ? `${Math.round(sale.compare_at_discount_percent)}% off`
      : dropped7d > 5
        ? `↓${dropped7d.toFixed(1)}% this week`
        : dropped30d > 10
          ? `↓${dropped30d.toFixed(1)}% this month`
          : null;

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4 flex gap-3">
        {sale.image_url ? (
          <img
            src={sale.image_url}
            alt={sale.product_name}
            className="w-12 h-12 object-cover rounded border shrink-0"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = "none";
            }}
          />
        ) : (
          <div className="w-12 h-12 rounded border bg-amber-50 flex items-center justify-center shrink-0">
            <span className="text-lg">☕</span>
          </div>
        )}
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm line-clamp-1">{sale.product_name}</p>
          <p className="text-xs text-muted-foreground">
            {sale.merchant_name} · {sale.variant_label}
          </p>
          <div className="flex items-center gap-2 mt-1">
            <span className="font-semibold text-sm">{fmtPrice(sale.current_price_cents)}</span>
            {badge && (
              <Badge variant="outline" className="text-xs text-green-700 border-green-300">
                {badge}
              </Badge>
            )}
          </div>
        </div>
        <a
          href={sale.product_url}
          target="_blank"
          rel="noopener noreferrer"
          className="shrink-0 self-center"
        >
          <Button variant="ghost" size="sm" className="text-xs">
            View →
          </Button>
        </a>
      </CardContent>
    </Card>
  );
}

function TodayPage() {
  const [shotStyle, setShotStyle] = useState("modern_58mm");
  const [quantityMode, setQuantityMode] = useState("12-18 oz");

  const { data, isLoading, refetch, isFetching } = useTodayBrief({
    shot_style: shotStyle,
    quantity_mode: quantityMode,
  });

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold">☕ Today</h1>
        <p className="text-muted-foreground">What should I buy right now?</p>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap gap-3">
        <div className="space-y-1">
          <label className="text-xs font-medium text-muted-foreground">Shot style</label>
          <Select value={shotStyle} onValueChange={setShotStyle}>
            <SelectTrigger className="w-44">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="modern_58mm">Modern 58mm</SelectItem>
              <SelectItem value="lever_49mm">Lever 49mm</SelectItem>
              <SelectItem value="turbo">Turbo shot</SelectItem>
              <SelectItem value="experimental">Experimental</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1">
          <label className="text-xs font-medium text-muted-foreground">Bag size</label>
          <Select value={quantityMode} onValueChange={setQuantityMode}>
            <SelectTrigger className="w-36">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="12-18 oz">12–18 oz</SelectItem>
              <SelectItem value="2lb">2 lb</SelectItem>
              <SelectItem value="5lb">5 lb</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-end">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
          >
            {isFetching ? "Refreshing…" : "Refresh"}
          </Button>
        </div>
      </div>

      {/* Top pick */}
      {isLoading ? (
        <Skeleton className="h-48 w-full rounded-xl" />
      ) : data?.wait_recommendation ? (
        <Card className="border-dashed">
          <CardContent className="py-8 text-center text-muted-foreground">
            <p className="text-3xl mb-3">⏸️</p>
            <p className="font-medium">Nothing worth buying right now</p>
            <p className="text-sm mt-1">
              No merchants meet the quality threshold for the current filters.
            </p>
          </CardContent>
        </Card>
      ) : data?.top_pick ? (
        <TopPickCard pick={data.top_pick} />
      ) : null}

      {/* Alternatives */}
      {!isLoading && data?.alternatives && data.alternatives.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            Alternatives
          </h2>
          {data.alternatives.map((alt, i) => (
            <SaleCard key={i} sale={{ ...alt, current_price_cents: alt.landed_price_cents, compare_at_discount_percent: 0, price_drop_7d_percent: 0, price_drop_30d_percent: 0, historical_low_cents: 0, reasons: alt.pros } as unknown as NonNullable<TodayBriefResult["notable_sales"]>[number]} />
          ))}
        </div>
      )}

      {/* Notable sales */}
      {!isLoading && data?.notable_sales && data.notable_sales.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            Notable Sales Right Now
          </h2>
          {data.notable_sales.map((sale, i) => (
            <SaleCard key={i} sale={sale} />
          ))}
        </div>
      )}
    </div>
  );
}
