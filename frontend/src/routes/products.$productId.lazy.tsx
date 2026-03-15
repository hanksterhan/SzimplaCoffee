import { createLazyFileRoute, Link } from "@tanstack/react-router";
import { useMemo } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { PriceHistoryChart } from "@/components/charts/PriceHistoryChart";
import { useMerchant } from "@/hooks/use-merchants";
import { useProduct, useProductOfferHistory } from "@/hooks/use-products";
import type { ProductVariantSchema, OfferSnapshotSchema } from "@/hooks/use-products";

export const Route = createLazyFileRoute("/products/$productId")({
  component: ProductDetailPage,
});

function formatPrice(cents: number) {
  return `$${(cents / 100).toFixed(2)}`;
}

function formatWeight(grams: number | null) {
  if (!grams) return "—";
  if (grams >= 907) return `${(grams / 453.6).toFixed(1)} lb`;
  if (grams >= 454) return `${(grams / 453.6).toFixed(1)} lb`;
  return `${grams}g`;
}

// Build variant history for PriceHistoryChart
function buildVariantHistory(
  variants: ProductVariantSchema[],
  offers: OfferSnapshotSchema[]
) {
  // The offers endpoint returns flat offers; map them by variant
  // For simplicity, attribute all flat offers to a combined "Price" line
  // (variant-level offers are in product.variants[].offers)
  const historyMap = new Map<
    number,
    { variantId: number; label: string; offers: Array<{
      id: number;
      observed_at: string;
      price_cents: number;
      compare_at_price_cents: number | null;
      is_on_sale: boolean;
      is_available: boolean;
      source_url: string;
    }> }
  >();

  // First, use variant-embedded offers
  variants.forEach((v) => {
    if (v.offers.length > 0) {
      historyMap.set(v.id, {
        variantId: v.id,
        label: v.label,
        offers: v.offers.map((o) => ({
          id: o.id,
          observed_at: o.observed_at,
          price_cents: o.price_cents,
          compare_at_price_cents: o.compare_at_price_cents,
          is_on_sale: o.is_on_sale,
          is_available: o.is_available,
          source_url: o.source_url,
        })),
      });
    }
  });

  // If no variant-embedded offers, use flat offers as a single line
  if (historyMap.size === 0 && offers.length > 0) {
    historyMap.set(-1, {
      variantId: -1,
      label: "Price",
      offers: offers.map((o) => ({
        id: o.id,
        observed_at: o.observed_at,
        price_cents: o.price_cents,
        compare_at_price_cents: o.compare_at_price_cents,
        is_on_sale: o.is_on_sale,
        is_available: o.is_available,
        source_url: o.source_url,
      })),
    });
  }

  return Array.from(historyMap.values());
}

function MetaTag({ label, value }: { label: string; value: string }) {
  if (!value) return null;
  return (
    <div className="text-sm">
      <span className="text-muted-foreground">{label}: </span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

function ProductDetailPage() {
  const { productId } = Route.useParams();
  const id = Number(productId);

  const { data: product, isLoading, error } = useProduct(id);
  const { data: offers = [] } = useProductOfferHistory(id);
  const { data: merchant } = useMerchant(product?.merchant_id ?? 0);

  const variantHistory = useMemo(() => {
    if (!product) return [];
    return buildVariantHistory(product.variants, offers);
  }, [product, offers]);

  if (isLoading) {
    return (
      <div className="space-y-4 max-w-4xl mx-auto">
        <Skeleton className="h-6 w-48" />
        <div className="flex gap-6">
          <Skeleton className="h-48 w-48 rounded-lg flex-shrink-0" />
          <div className="flex-1 space-y-3">
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-4 w-2/3" />
            <Skeleton className="h-4 w-1/3" />
          </div>
        </div>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="py-16 text-center space-y-4">
        <p className="text-muted-foreground text-lg">Product not found.</p>
        <Link to="/products">
          <Button variant="outline">← Back to Products</Button>
        </Link>
      </div>
    );
  }

  // Find cheapest available variant
  const availableVariants = product.variants.filter((v) => v.is_available);
  const cheapestVariant = availableVariants.reduce<ProductVariantSchema | null>(
    (min, v) => {
      if (!v.latest_offer) return min;
      if (!min?.latest_offer) return v;
      return v.latest_offer.price_cents < min.latest_offer.price_cents ? v : min;
    },
    null
  );

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-muted-foreground flex-wrap">
        <Link to="/products" className="hover:underline">
          Products
        </Link>
        <span>/</span>
        {merchant && (
          <>
            <Link
              to="/merchants/$merchantId"
              params={{ merchantId: String(product.merchant_id) }}
              className="hover:underline"
            >
              {merchant.name}
            </Link>
            <span>/</span>
          </>
        )}
        <span className="text-foreground font-medium line-clamp-1">{product.name}</span>
      </nav>

      {/* Product header */}
      <div className="flex flex-col sm:flex-row gap-6">
        {/* Image */}
        <div className="w-full sm:w-48 flex-shrink-0">
          <div className="aspect-square rounded-lg bg-muted overflow-hidden">
            {product.image_url ? (
              <img
                src={product.image_url}
                alt={product.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-6xl text-muted-foreground/30">
                ☕
              </div>
            )}
          </div>
        </div>

        {/* Details */}
        <div className="flex-1 space-y-3">
          <div>
            <div className="flex items-start gap-2 flex-wrap">
              <h1 className="text-2xl font-bold leading-tight">{product.name}</h1>
              {product.is_espresso_recommended && (
                <Badge className="bg-amber-900 text-amber-100 shrink-0">
                  ☕ Espresso Recommended
                </Badge>
              )}
              {product.is_single_origin && (
                <Badge variant="outline" className="shrink-0">
                  Single Origin
                </Badge>
              )}
            </div>
            {merchant && (
              <Link
                to="/merchants/$merchantId"
                params={{ merchantId: String(product.merchant_id) }}
                className="text-sm text-blue-600 hover:underline"
              >
                {merchant.name} ↗
              </Link>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-1">
            <MetaTag label="Origin" value={product.origin_text} />
            <MetaTag label="Process" value={product.process_text} />
            <MetaTag label="Variety" value={product.variety_text} />
            <MetaTag label="Roast" value={product.roast_cues} />
          </div>

          {product.tasting_notes_text && (
            <div className="text-sm">
              <span className="text-muted-foreground">Tasting notes: </span>
              <span className="font-medium">{product.tasting_notes_text}</span>
            </div>
          )}

          {/* Price + buy button */}
          <div className="flex items-center gap-4 pt-2">
            {cheapestVariant?.latest_offer && (
              <div>
                <span className="text-2xl font-bold text-amber-900">
                  {formatPrice(cheapestVariant.latest_offer.price_cents)}
                </span>
                {cheapestVariant.weight_grams && (
                  <span className="text-sm text-muted-foreground ml-1">
                    / {formatWeight(cheapestVariant.weight_grams)}
                  </span>
                )}
              </div>
            )}
            <a href={product.product_url} target="_blank" rel="noreferrer">
              <Button className="bg-amber-800 hover:bg-amber-900 text-white">
                Buy ↗
              </Button>
            </a>
          </div>
        </div>
      </div>

      <Separator />

      {/* Variants table */}
      {product.variants.length > 0 && (
        <div className="space-y-3">
          <h2 className="font-semibold text-lg">Variants</h2>
          <div className="rounded-md border overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Label</TableHead>
                  <TableHead>Weight</TableHead>
                  <TableHead>Price</TableHead>
                  <TableHead>Availability</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {product.variants.map((v) => {
                  const isCheapest = cheapestVariant?.id === v.id;
                  return (
                    <TableRow
                      key={v.id}
                      className={isCheapest ? "bg-amber-50/50" : undefined}
                    >
                      <TableCell className="font-medium">
                        {v.label}
                        {isCheapest && availableVariants.length > 1 && (
                          <Badge variant="outline" className="ml-2 text-xs text-green-700 border-green-300">
                            Best value
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>{formatWeight(v.weight_grams)}</TableCell>
                      <TableCell>
                        {v.latest_offer ? (
                          <span className="font-semibold">
                            {formatPrice(v.latest_offer.price_cents)}
                            {v.latest_offer.is_on_sale && (
                              <Badge className="ml-2 bg-red-100 text-red-700 border-red-200 text-xs">
                                Sale
                              </Badge>
                            )}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <span
                          className={`text-sm font-medium ${
                            v.is_available ? "text-green-600" : "text-gray-400"
                          }`}
                        >
                          {v.is_available ? "● In stock" : "● Out of stock"}
                        </span>
                      </TableCell>
                      <TableCell>
                        {v.is_available && (
                          <a
                            href={product.product_url}
                            target="_blank"
                            rel="noreferrer"
                          >
                            <Button size="sm" variant="outline">
                              Buy ↗
                            </Button>
                          </a>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        </div>
      )}

      {/* Price history chart */}
      <div className="space-y-3">
        <h2 className="font-semibold text-lg">Price History</h2>
        <div className="rounded-lg border p-4">
          {variantHistory.length === 0 ? (
            <div className="flex items-center justify-center text-muted-foreground text-sm py-8">
              No price history available yet
            </div>
          ) : (
            <PriceHistoryChart variants={variantHistory} height={280} />
          )}
        </div>
      </div>

      {/* Back link */}
      <div className="flex gap-3 pt-2">
        <Link to="/products">
          <Button variant="outline">← Back to Products</Button>
        </Link>
        {merchant && (
          <Link
            to="/merchants/$merchantId"
            params={{ merchantId: String(product.merchant_id) }}
          >
            <Button variant="outline">View {merchant.name}</Button>
          </Link>
        )}
      </div>
    </div>
  );
}
