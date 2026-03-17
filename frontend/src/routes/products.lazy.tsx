import { createLazyFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { Check, ChevronDown, ExternalLink } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  useProduct,
  useProductMerchantOptions,
  useProductSearch,
  type ProductDetail,
  type ProductSort,
  type ProductSummary,
} from "@/hooks/use-products";
import { useIntersectionObserver } from "@/hooks/use-intersection-observer";

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

type ProductCardSummary = ProductSummary & {
  latest_price_cents?: number | null;
  latest_compare_at_price_cents?: number | null;
  latest_discount_percent?: number | null;
  primary_weight_grams?: number | null;
  primary_is_whole_bean?: boolean;
};

const CATEGORY_OPTIONS = [
  { value: "coffee", label: "☕ Coffee Beans" },
  { value: "cold_brew", label: "🧊 Cold Brew" },
  { value: "instant", label: "⚡ Instant" },
  { value: "gift", label: "🎁 Gift / Subscription" },
  { value: "merch", label: "👕 Merch" },
  { value: "equipment", label: "⚙️ Equipment" },
  { value: "tea", label: "🍵 Tea" },
  { value: "all", label: "🌐 All Categories" },
] as const;

function formatPrice(cents: number) {
  return `$${(cents / 100).toFixed(2)}`;
}

function formatWeight(grams: number | null | undefined) {
  if (!grams) return null;
  const ounces = grams / 28.3495;
  if (ounces >= 16) {
    return `${(ounces / 16).toFixed(1)} lb`;
  }
  return `${Math.round(ounces)} oz`;
}

function formatPricePerOz(cents: number | null | undefined, grams: number | null | undefined) {
  if (!cents || !grams) return null;
  const ounces = grams / 28.3495;
  if (!ounces) return null;
  return `$${((cents / 100) / ounces).toFixed(2)}/oz`;
}

function buildTags(product: Pick<ProductDetail, "product_category" | "origin_text" | "process_text" | "variety_text" | "roast_cues" | "tasting_notes_text" | "is_single_origin" | "is_espresso_recommended">) {
  const tags = [
    product.product_category,
    product.is_single_origin ? "single origin" : null,
    product.is_espresso_recommended ? "espresso" : null,
    product.origin_text || null,
    product.process_text || null,
    product.variety_text || null,
    product.roast_cues || null,
  ].filter(Boolean) as string[];

  return Array.from(new Set(tags));
}

function toggleCategory(current: string[], value: string) {
  if (value === "all") return ["all"];
  const withoutAll = current.filter((item) => item !== "all");
  const exists = withoutAll.includes(value);
  const next = exists ? withoutAll.filter((item) => item !== value) : [...withoutAll, value];
  return next.length > 0 ? next : ["coffee"];
}

function toggleMerchant(current: number[], value: number) {
  const exists = current.includes(value);
  return exists ? current.filter((item) => item !== value) : [...current, value];
}

function ProductCard({ product, onClick }: { product: ProductCardSummary; onClick: () => void }) {
  const weightLabel = formatWeight(product.primary_weight_grams);
  const pricePerOzLabel = formatPricePerOz(product.latest_price_cents, product.primary_weight_grams);

  return (
    <button
      type="button"
      onClick={onClick}
      className="text-left rounded-lg border bg-card hover:shadow-md transition-all overflow-hidden group flex flex-col w-full"
    >
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
            <Badge className="bg-amber-900 text-amber-100 text-xs px-1.5 py-0 h-5">☕ Espresso</Badge>
          </div>
        )}
      </div>

      <div className="p-3 space-y-2 flex-1 flex flex-col min-h-0">
        <div className="space-y-1">
          <p className="font-semibold text-sm leading-tight line-clamp-2">{product.name}</p>
          {product.merchant_name && (
            <p className="text-xs text-muted-foreground truncate">{product.merchant_name}</p>
          )}
        </div>

        <div className="mt-auto flex items-end justify-between gap-3">
          <div className="min-w-0">
            {product.latest_price_cents ? (
              <>
                <p className="font-bold text-sm text-amber-900">{formatPrice(product.latest_price_cents)}</p>
                {product.primary_is_whole_bean && (weightLabel || pricePerOzLabel) && (
                  <p className="text-xs text-muted-foreground">
                    {[weightLabel, pricePerOzLabel].filter(Boolean).join(" • ")}
                  </p>
                )}
              </>
            ) : (
              <p className="text-sm text-muted-foreground">Price unavailable</p>
            )}
          </div>
          <span className={`text-[11px] whitespace-nowrap ${product.is_active ? "text-green-600" : "text-muted-foreground"}`}>
            {product.is_active ? "● In stock" : "● Unavailable"}
          </span>
        </div>
      </div>
    </button>
  );
}

function ProductCardSkeleton() {
  return (
    <div className="rounded-lg border overflow-hidden">
      <Skeleton className="aspect-square w-full" />
      <div className="p-3 space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
        <Skeleton className="h-3 w-1/3" />
      </div>
    </div>
  );
}

function ProductQuickView({ productId }: { productId: number | null }) {
  const { data: product, isLoading } = useProduct(productId);

  const cheapestVariant = useMemo(() => {
    if (!product) return null;
    const priced = product.variants.filter((variant) => variant.latest_offer);
    if (priced.length === 0) return null;
    const wholeBean = priced.filter((variant) => variant.is_whole_bean && variant.weight_grams);
    const pool = wholeBean.length > 0 ? wholeBean : priced;
    return pool.reduce((best, variant) => {
      if (!best?.latest_offer) return variant;
      return variant.latest_offer!.price_cents < best.latest_offer.price_cents ? variant : best;
    }, pool[0]);
  }, [product]);

  if (!productId) return null;

  if (isLoading || !product) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-6 w-2/3" />
        <Skeleton className="h-4 w-1/3" />
        <Skeleton className="h-48 w-full rounded-lg" />
        <Skeleton className="h-24 w-full rounded-lg" />
      </div>
    );
  }

  const tags = buildTags(product);
  const description = product.tasting_notes_text || "No long-form product description is available yet, but the metadata below should still help you evaluate it quickly.";
  const quickViewPricePerOz = cheapestVariant?.latest_offer
    ? formatPricePerOz(cheapestVariant.latest_offer.price_cents, cheapestVariant.weight_grams)
    : null;

  return (
    <div className="space-y-5 max-h-[80vh] overflow-y-auto pr-1">
      <div className="flex flex-col gap-4 sm:flex-row">
        <div className="w-full sm:w-40 flex-shrink-0">
          <div className="aspect-square rounded-lg bg-muted overflow-hidden">
            {product.image_url ? (
              <img src={product.image_url} alt={product.name} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-5xl text-muted-foreground/30">☕</div>
            )}
          </div>
        </div>
        <div className="flex-1 space-y-3 min-w-0">
          <DialogHeader className="space-y-2 text-left">
            <DialogTitle className="text-xl leading-tight">{product.name}</DialogTitle>
            <DialogDescription className="text-sm">
              {product.merchant_name || "Unknown merchant"}
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-wrap gap-2">
            {tags.map((tag) => (
              <Badge key={tag} variant="outline" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-3 text-sm">
            {cheapestVariant?.latest_offer && (
              <span className="font-semibold text-amber-900">
                {formatPrice(cheapestVariant.latest_offer.price_cents)}
                {[formatWeight(cheapestVariant.weight_grams), quickViewPricePerOz].filter(Boolean).length > 0
                  ? ` / ${[formatWeight(cheapestVariant.weight_grams), quickViewPricePerOz].filter(Boolean).join(" • ")}`
                  : ""}
              </span>
            )}
            <span className={product.is_active ? "text-green-600" : "text-muted-foreground"}>
              {product.is_active ? "● In stock" : "● Unavailable"}
            </span>
          </div>
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="font-medium">Description</h3>
        <p className="text-sm text-muted-foreground leading-6">{description}</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
        {product.origin_text && <div><span className="text-muted-foreground">Origin:</span> {product.origin_text}</div>}
        {product.process_text && <div><span className="text-muted-foreground">Process:</span> {product.process_text}</div>}
        {product.variety_text && <div><span className="text-muted-foreground">Variety:</span> {product.variety_text}</div>}
        {product.roast_cues && <div><span className="text-muted-foreground">Roast:</span> {product.roast_cues}</div>}
      </div>

      {product.variants.length > 0 && (
        <div className="space-y-2">
          <h3 className="font-medium">Variants</h3>
          <div className="space-y-2">
            {product.variants.map((variant) => {
              const variantPricePerOz = variant.latest_offer
                ? formatPricePerOz(variant.latest_offer.price_cents, variant.weight_grams)
                : null;

              return (
                <div key={variant.id} className="rounded-md border p-3 flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="font-medium text-sm truncate">{variant.label}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatWeight(variant.weight_grams) || "Size unavailable"}
                      {variantPricePerOz ? ` • ${variantPricePerOz}` : ""}
                      {variant.is_whole_bean ? " • whole bean" : " • not whole bean"}
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="font-medium text-sm">
                      {variant.latest_offer ? formatPrice(variant.latest_offer.price_cents) : "—"}
                    </p>
                    <p className={`text-xs ${variant.is_available ? "text-green-600" : "text-muted-foreground"}`}>
                      {variant.is_available ? "In stock" : "Unavailable"}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="flex flex-wrap gap-2 pt-1">
        <a href={product.product_url} target="_blank" rel="noreferrer">
          <Button className="gap-2">
            View product <ExternalLink className="h-4 w-4" />
          </Button>
        </a>
        <Link to="/products/$productId" params={{ productId: String(product.id) }}>
          <Button variant="outline">Open full page</Button>
        </Link>
      </div>
    </div>
  );
}

function ProductsPage() {
  const [inputValue, setInputValue] = useState("");
  const [categories, setCategories] = useState<string[]>(["coffee"]);
  const [selectedMerchants, setSelectedMerchants] = useState<number[]>([]);
  const [sortBy, setSortBy] = useState<ProductSort>("featured");
  const [selectedProductId, setSelectedProductId] = useState<number | null>(null);
  const [categoriesOpen, setCategoriesOpen] = useState(false);
  const [merchantsOpen, setMerchantsOpen] = useState(false);
  const [sortOpen, setSortOpen] = useState(false);
  const debouncedQ = useDebounce(inputValue, 350);
  const inputRef = useRef<HTMLInputElement>(null);



  const { data, isLoading, isFetchingNextPage, hasNextPage, fetchNextPage } = useProductSearch({
    q: debouncedQ,
    categories,
    merchantIds: selectedMerchants,
    sort: sortBy,
  });
  const { data: merchantOptionRows } = useProductMerchantOptions(debouncedQ, categories);

  const products = (data?.pages.flatMap((page) => page.items) ?? []) as ProductCardSummary[];
  const merchantOptions = merchantOptionRows ?? [];
  const totalLoaded = products.length;
  const selectedLabels = categories.includes("all")
    ? ["🌐 All Categories"]
    : CATEGORY_OPTIONS.filter((option) => categories.includes(option.value)).map((option) => option.label);
  const categoryMenuLabel = categories.includes("all")
    ? "All categories"
    : selectedLabels.length > 0
      ? `${selectedLabels.length} selected`
      : "Select categories";
  const merchantMenuLabel = selectedMerchants.length > 0
    ? `${selectedMerchants.length} selected`
    : "All merchants";

  const handleLoadMore = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  const loadMoreRef = useIntersectionObserver(handleLoadMore, {
    enabled: hasNextPage && !isFetchingNextPage,
    rootMargin: "200px",
  });

  return (
    <>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">📦 Products</h1>
          <p className="text-muted-foreground text-sm">
            Browse specialty coffee products with backend-truth sorting and filtering
          </p>
        </div>

        <div className="space-y-3 max-w-4xl">
          <div className="relative max-w-2xl">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">🔍</span>
            <Input
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Search by product name…"
              className="pl-8"
            />
          </div>

          <div className="flex flex-wrap gap-2 items-center">
            <DropdownMenu modal={false} open={categoriesOpen} onOpenChange={setCategoriesOpen}>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="outline"
                  className="gap-2"
                  onClick={() => setCategoriesOpen((v) => !v)}
                >
                  Categories
                  <span className="text-muted-foreground">{categoryMenuLabel}</span>
                  <ChevronDown className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-72">
                <DropdownMenuLabel>Filter product categories</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {CATEGORY_OPTIONS.map((option) => {
                  const checked = categories.includes(option.value) || (option.value === "all" && categories.includes("all"));
                  return (
                    <DropdownMenuCheckboxItem
                      key={option.value}
                      checked={checked}
                      onCheckedChange={() => setCategories((current) => toggleCategory(current, option.value))}
                    >
                      <span>{option.label}</span>
                    </DropdownMenuCheckboxItem>
                  );
                })}
              </DropdownMenuContent>
            </DropdownMenu>

            <DropdownMenu modal={false} open={merchantsOpen} onOpenChange={setMerchantsOpen}>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="gap-2" onClick={() => setMerchantsOpen((v) => !v)}>
                  Merchants
                  <span className="text-muted-foreground">{merchantMenuLabel}</span>
                  <ChevronDown className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-72 max-h-80 overflow-y-auto">
                <DropdownMenuLabel>Filter merchants</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {merchantOptions.length === 0 ? (
                  <div className="px-2 py-1.5 text-sm text-muted-foreground">No merchants loaded yet</div>
                ) : (
                  merchantOptions.map((merchant) => {
                    const checked = selectedMerchants.includes(merchant.merchant_id);
                    return (
                      <DropdownMenuCheckboxItem
                        key={merchant.merchant_id}
                        checked={checked}
                        onCheckedChange={() => setSelectedMerchants((current) => toggleMerchant(current, merchant.merchant_id))}
                      >
                        <span className="truncate">{merchant.merchant_name}</span>
                      </DropdownMenuCheckboxItem>
                    );
                  })
                )}
              </DropdownMenuContent>
            </DropdownMenu>

            <DropdownMenu modal={false} open={sortOpen} onOpenChange={setSortOpen}>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="gap-2" onClick={() => setSortOpen((v) => !v)}>
                  Sort
                  <span className="text-muted-foreground">{sortBy.replaceAll("_", " ")}</span>
                  <ChevronDown className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56">
                <DropdownMenuLabel>Sort products</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {[
                  ["featured", "Featured"],
                  ["merchant", "Merchant"],
                  ["price_low", "Price: low to high"],
                  ["price_high", "Price: high to low"],
                  ["price_per_oz_low", "Price/oz: low to high"],
                  ["price_per_oz_high", "Price/oz: high to low"],
                  ["discount", "Discount: best first"],
                ].map(([value, label]) => (
                  <button
                    key={value}
                    type="button"
                    className={`flex w-full items-center justify-between rounded-sm px-2 py-1.5 text-sm hover:bg-accent ${sortBy === value ? "bg-accent" : ""}`}
                    onClick={() => {
                      console.log("[Filter:Sort] clicked — value:", value);
                      setSortBy(value as typeof sortBy);
                    }}
                  >
                    <span>{label}</span>
                    {sortBy === value && <Check className="h-4 w-4 text-green-600" />}
                  </button>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>

            {inputValue && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setInputValue("");
                  inputRef.current?.focus();
                }}
              >
                Clear search
              </Button>
            )}
          </div>
        </div>

        <div className="flex items-center justify-between gap-3 flex-wrap">
          <p className="text-sm text-muted-foreground">
            {isLoading ? (
              "Loading…"
            ) : debouncedQ ? (
              <>
                Showing {totalLoaded} result{totalLoaded !== 1 ? "s" : ""} for <span className="font-medium text-foreground">“{debouncedQ}”</span>
              </>
            ) : (
              <>
                Showing {totalLoaded}{hasNextPage ? "+" : ""} products
              </>
            )}
          </p>
          <div className="flex flex-wrap gap-1" />
        </div>

        {isLoading ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {Array.from({ length: 24 }).map((_, i) => (
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
              {debouncedQ ? "Try different search terms or category combinations" : "Add merchants and run crawls to populate the catalog"}
            </p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {products.map((product) => (
                <ProductCard key={product.id} product={product} onClick={() => setSelectedProductId(product.id)} />
              ))}
            </div>

            {isFetchingNextPage && (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {Array.from({ length: 3 }).map((_, i) => (
                  <ProductCardSkeleton key={i} />
                ))}
              </div>
            )}

            {!hasNextPage && !isLoading && (
              <p className="text-center text-sm text-muted-foreground py-4">
                ✓ All {totalLoaded} products shown
              </p>
            )}
            <div ref={loadMoreRef} className="h-1" />
          </>
        )}
      </div>

      <Dialog open={selectedProductId !== null} onOpenChange={(open) => !open && setSelectedProductId(null)}>
        <DialogContent className="max-w-3xl">
          <ProductQuickView productId={selectedProductId} />
        </DialogContent>
      </Dialog>
    </>
  );
}
