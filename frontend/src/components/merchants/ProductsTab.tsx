import { useState, useCallback } from "react";
import { useMerchantProducts } from "@/hooks/use-merchants";
import { useProductDetail } from "@/hooks/use-product-offers";
import { useIntersectionObserver } from "@/hooks/use-intersection-observer";
import { PriceHistoryChart } from "@/components/charts/PriceHistoryChart";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ChevronDown, ChevronRight } from "lucide-react";
import type { ProductSummary } from "@/hooks/use-products";

interface ProductsTabProps {
  merchantId: number;
}

interface ExpandedProductRowProps {
  productId: number;
}

function ExpandedProductRow({ productId }: ExpandedProductRowProps) {
  const { data: detail, isLoading } = useProductDetail(productId);

  if (isLoading) {
    return (
      <div className="px-4 py-3 bg-muted/20 border-t">
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (!detail?.variants?.length) {
    return (
      <div className="px-4 py-3 bg-muted/20 border-t text-sm text-muted-foreground">
        No variant data available.
      </div>
    );
  }

  const variants = detail.variants.map((v) => ({
    variantId: v.id,
    label: v.label,
    offers: (v.offers ?? []).map((o) => ({
      id: o.id,
      observed_at: o.observed_at,
      price_cents: o.price_cents,
      compare_at_price_cents: o.compare_at_price_cents ?? null,
      is_on_sale: o.is_on_sale,
      is_available: o.is_available,
    })),
  }));

  const hasAnyOffers = variants.some((v) => v.offers.length > 0);

  return (
    <div className="px-4 py-4 bg-amber-50/30 border-t border-amber-100">
      <div className="mb-2">
        <span className="text-xs font-semibold text-amber-800 uppercase tracking-wider">
          Price History
        </span>
        {!hasAnyOffers && (
          <span className="ml-2 text-xs text-muted-foreground">No offers recorded yet</span>
        )}
      </div>
      {hasAnyOffers ? (
        <PriceHistoryChart variants={variants} height={220} />
      ) : (
        <div className="h-12 flex items-center justify-center text-sm text-muted-foreground">
          No price history available
        </div>
      )}
      {/* Variant summary table */}
      <div className="mt-3 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
        {detail.variants.map((v) => {
          const latest = v.latest_offer;
          return (
            <div
              key={v.id}
              className="text-xs rounded border border-amber-100 bg-white/60 px-2 py-1.5 space-y-0.5"
            >
              <div className="font-medium text-foreground truncate">{v.label}</div>
              {latest ? (
                <>
                  <div className="text-green-700 font-semibold">
                    ${(latest.price_cents / 100).toFixed(2)}
                    {latest.is_on_sale && (
                      <span className="ml-1 text-orange-500 font-normal">SALE</span>
                    )}
                  </div>
                  {v.weight_grams && (
                    <div className="text-muted-foreground">
                      {(v.weight_grams / 28.3495).toFixed(0)} oz
                    </div>
                  )}
                </>
              ) : (
                <div className="text-muted-foreground">No price</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

const CATEGORY_OPTIONS = [
  { value: "coffee", label: "☕ Coffee Beans" },
  { value: "cold_brew", label: "🧊 Cold Brew" },
  { value: "instant", label: "⚡ Instant" },
  { value: "gift", label: "🎁 Gift / Subscription" },
  { value: "merch", label: "👕 Merch" },
  { value: "equipment", label: "⚙️ Equipment" },
  { value: "tea", label: "🍵 Tea" },
  { value: "all", label: "🌐 All" },
];

export function ProductsTab({ merchantId }: ProductsTabProps) {
  const [category, setCategory] = useState("coffee");
  const {
    data,
    isLoading,
    isFetchingNextPage,
    hasNextPage,
    fetchNextPage,
  } = useMerchantProducts(merchantId, category);
  const [expandedProductId, setExpandedProductId] = useState<number | null>(null);

  // Flatten all pages
  const products: ProductSummary[] = data?.pages.flatMap((page) => page.items) ?? [];
  const totalLoaded = products.length;
  const activeCount = products.filter((p) => p.is_active).length;

  const handleLoadMore = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  const loadMoreRef = useIntersectionObserver(handleLoadMore, {
    enabled: hasNextPage && !isFetchingNextPage,
    rootMargin: "200px",
  });

  if (isLoading) {
    return (
      <div className="space-y-2 mt-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    );
  }

  if (!products.length && !isLoading) {
    return (
      <div className="py-12 text-center text-muted-foreground">
        No products found for this merchant.
      </div>
    );
  }

  const handleRowClick = (productId: number) => {
    setExpandedProductId((prev) => (prev === productId ? null : productId));
  };

  return (
    <div className="mt-4 space-y-2">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <p className="text-sm text-muted-foreground">
          Showing {totalLoaded}{hasNextPage ? "+" : ""} products ({activeCount} active) —{" "}
          <span className="text-xs">click a row to see price history</span>
        </p>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="rounded-md border border-input bg-background px-3 py-1.5 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
        >
          {CATEGORY_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-6"></TableHead>
            <TableHead className="w-12"></TableHead>
            <TableHead>Name</TableHead>
            <TableHead>Origin</TableHead>
            <TableHead>Process</TableHead>
            <TableHead>Espresso</TableHead>
            <TableHead>Active</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {products.map((p) => (
            <>
              <TableRow
                key={p.id}
                className="cursor-pointer hover:bg-amber-50/50 transition-colors"
                onClick={() => handleRowClick(p.id)}
              >
                <TableCell className="text-muted-foreground w-6 pr-0">
                  {expandedProductId === p.id ? (
                    <ChevronDown className="h-3.5 w-3.5" />
                  ) : (
                    <ChevronRight className="h-3.5 w-3.5" />
                  )}
                </TableCell>
                <TableCell>
                  {p.image_url ? (
                    <img
                      src={p.image_url}
                      alt={p.name}
                      className="w-8 h-8 object-cover rounded"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = "none";
                      }}
                    />
                  ) : (
                    <div className="w-8 h-8 bg-muted rounded flex items-center justify-center text-xs">
                      ☕
                    </div>
                  )}
                </TableCell>
                <TableCell className="max-w-48">
                  <a
                    href={p.product_url}
                    target="_blank"
                    rel="noreferrer"
                    className="font-medium hover:underline text-blue-600 text-sm block truncate"
                    onClick={(e) => e.stopPropagation()}
                    title={p.name}
                  >
                    {p.name}
                  </a>
                </TableCell>
                <TableCell className="text-sm text-muted-foreground max-w-24 truncate" title={p.origin_text || ""}>
                  {p.origin_text || "—"}
                </TableCell>
                <TableCell className="text-sm text-muted-foreground max-w-24 truncate" title={p.process_text || ""}>
                  {p.process_text || "—"}
                </TableCell>
                <TableCell>
                  {p.is_espresso_recommended && (
                    <Badge
                      variant="outline"
                      className="bg-amber-50 text-amber-700 border-amber-200 text-xs"
                    >
                      ☕ Espresso
                    </Badge>
                  )}
                </TableCell>
                <TableCell>
                  <span className={`text-sm ${p.is_active ? "text-green-600" : "text-gray-400"}`}>
                    {p.is_active ? "✓" : "—"}
                  </span>
                </TableCell>
              </TableRow>
              {expandedProductId === p.id && (
                <TableRow key={`${p.id}-expanded`} className="hover:bg-transparent">
                  <TableCell colSpan={7} className="p-0">
                    <ExpandedProductRow productId={p.id} />
                  </TableCell>
                </TableRow>
              )}
            </>
          ))}
        </TableBody>
      </Table>

      {/* Inline skeleton rows while fetching next page */}
      {isFetchingNextPage && (
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      )}

      {/* End state */}
      {!hasNextPage && totalLoaded > 0 && (
        <p className="text-center text-sm text-muted-foreground py-2">
          ✓ All {totalLoaded} products shown
        </p>
      )}

      {/* Sentinel */}
      <div ref={loadMoreRef} className="h-1" />
    </div>
  );
}
