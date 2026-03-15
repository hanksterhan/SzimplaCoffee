import { createLazyFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useEffect, useRef } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useProductSearch, type ProductSummary } from "@/hooks/use-products";

export const Route = createLazyFileRoute("/products")({
  component: ProductsPage,
});

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}

function EspressoBadge() {
  return (
    <Badge className="bg-amber-900 text-amber-100 text-xs px-1.5 py-0 h-5">
      ☕ Espresso
    </Badge>
  );
}

function formatPrice(cents: number) {
  return `$${(cents / 100).toFixed(2)}`;
}

function ProductCard({ product }: { product: ProductSummary }) {
  const navigate = useNavigate();
  const latestOffer = product as ProductSummary & {
    latest_price_cents?: number;
    latest_offer?: { price_cents: number };
  };

  return (
    <div
      className="rounded-lg border bg-card hover:shadow-md transition-all cursor-pointer overflow-hidden group flex flex-col"
      onClick={() =>
        navigate({
          to: "/products/$productId",
          params: { productId: String(product.id) },
        })
      }
    >
      {/* Image */}
      <div className="aspect-square bg-muted relative overflow-hidden">
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={product.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = "none";
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-4xl text-muted-foreground/30">
            ☕
          </div>
        )}
        {product.is_espresso_recommended && (
          <div className="absolute top-2 right-2">
            <EspressoBadge />
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-3 space-y-1.5 flex-1 flex flex-col min-h-0">
        <p className="font-semibold text-sm leading-tight line-clamp-2">{product.name}</p>
        {product.merchant_name && (
          <p className="text-xs text-muted-foreground/70 truncate">{product.merchant_name}</p>
        )}

        <div className="flex flex-wrap gap-1 overflow-hidden max-h-6">
          {product.origin_text && (
            <Badge variant="outline" className="text-xs px-1.5 py-0 h-5 max-w-[100px] truncate block">
              {product.origin_text}
            </Badge>
          )}
          {product.process_text && (
            <Badge variant="secondary" className="text-xs px-1.5 py-0 h-5 max-w-[100px] truncate block">
              {product.process_text}
            </Badge>
          )}
        </div>

        {product.tasting_notes_text && (
          <p className="text-xs text-muted-foreground line-clamp-1">
            {product.tasting_notes_text}
          </p>
        )}

        <div className="flex items-center justify-between pt-1">
          <span className="text-xs text-muted-foreground">
            {product.is_active ? (
              <span className="text-green-600 font-medium">● In stock</span>
            ) : (
              <span className="text-gray-400">● Unavailable</span>
            )}
          </span>
          {(latestOffer.latest_price_cents || latestOffer.latest_offer?.price_cents) && (
            <span className="font-bold text-sm text-amber-900">
              {formatPrice(latestOffer.latest_price_cents ?? latestOffer.latest_offer!.price_cents)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

function ProductCardSkeleton() {
  return (
    <div className="rounded-lg border overflow-hidden">
      <Skeleton className="aspect-square w-full" />
      <div className="p-3 space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
        <Skeleton className="h-3 w-full" />
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
  { value: "all", label: "🌐 All Categories" },
];

function ProductsPage() {
  const [inputValue, setInputValue] = useState("");
  const [category, setCategory] = useState("coffee");
  const [page, setPage] = useState(1);
  const debouncedQ = useDebounce(inputValue, 350);
  const inputRef = useRef<HTMLInputElement>(null);

  // Reset to page 1 when search or category changes
  useEffect(() => {
    setPage(1);
  }, [debouncedQ, category]);

  const { data, isLoading, isFetching } = useProductSearch(debouncedQ, page, 24, category);

  const products = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / 24);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">📦 Products</h1>
        <p className="text-muted-foreground text-sm">
          Browse {total > 0 ? `${total} ` : ""}specialty coffee products
        </p>
      </div>

      {/* Search + Filter bar */}
      <div className="flex flex-wrap gap-2 max-w-2xl">
        <div className="relative flex-1 min-w-48">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">
            🔍
          </span>
          <Input
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Search by name, origin, process, tasting notes…"
            className="pl-8"
          />
        </div>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
        >
          {CATEGORY_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        {inputValue && (
          <Button
            variant="outline"
            onClick={() => {
              setInputValue("");
              inputRef.current?.focus();
            }}
          >
            Clear
          </Button>
        )}
      </div>

      {/* Results count + status */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {isLoading ? (
            "Loading…"
          ) : debouncedQ ? (
            <>
              {total} result{total !== 1 ? "s" : ""} for{" "}
              <span className="font-medium text-foreground">"{debouncedQ}"</span>
              {category !== "all" && (
                <span className="text-muted-foreground/70"> in {CATEGORY_OPTIONS.find(o => o.value === category)?.label ?? category}</span>
              )}
            </>
          ) : (
            <>
              {total} {category !== "all" ? (CATEGORY_OPTIONS.find(o => o.value === category)?.label ?? category) + " " : ""}products
            </>
          )}
          {isFetching && !isLoading && (
            <span className="ml-2 text-muted-foreground/60">↻</span>
          )}
        </p>

        {totalPages > 1 && (
          <div className="flex items-center gap-2 text-sm">
            <Button
              size="sm"
              variant="outline"
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
            >
              ← Prev
            </Button>
            <span className="text-muted-foreground">
              {page} / {totalPages}
            </span>
            <Button
              size="sm"
              variant="outline"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next →
            </Button>
          </div>
        )}
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {Array.from({ length: 12 }).map((_, i) => (
            <ProductCardSkeleton key={i} />
          ))}
        </div>
      ) : products.length === 0 ? (
        <div className="rounded-lg border border-dashed p-16 text-center text-muted-foreground">
          <p className="text-4xl mb-3">📦</p>
          <p className="font-medium">
            {debouncedQ ? "No products match your search" : "No products yet"}
          </p>
          <p className="text-sm mt-1">
            {debouncedQ
              ? "Try different search terms"
              : "Add merchants and run crawls to populate the catalog"}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {products.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      )}

      {/* Bottom pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <Button
            variant="outline"
            disabled={page === 1}
            onClick={() => {
              setPage((p) => p - 1);
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
          >
            ← Previous
          </Button>
          <span className="flex items-center text-sm text-muted-foreground px-4">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="outline"
            disabled={page >= totalPages}
            onClick={() => {
              setPage((p) => p + 1);
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
          >
            Next →
          </Button>
        </div>
      )}
    </div>
  );
}
