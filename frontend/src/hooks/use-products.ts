import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import type { components } from "@/api/schema";

export type ProductSummary = components["schemas"]["ProductSummary"];
export type ProductDetail = components["schemas"]["ProductDetail"];
export type ProductVariantSchema = components["schemas"]["ProductVariantSchema"];
export type OfferSnapshotSchema = components["schemas"]["OfferSnapshotSchema"];
export type CursorPageProductSummary = components["schemas"]["CursorPage_ProductSummary_"];
export type ProductMerchantOption = { merchant_id: number; merchant_name: string };
export type ProductSort =
  | "featured"
  | "quality"
  | "freshness"
  | "merchant"
  | "price_low"
  | "price_high"
  | "price_per_oz_low"
  | "price_per_oz_high"
  | "discount";

export type ProductSearchParams = {
  q: string;
  categories?: string[];
  merchantIds?: number[];
  sort?: ProductSort;
};

export function useProductSearch({
  q,
  categories = ["coffee"],
  merchantIds = [],
  sort = "featured",
}: ProductSearchParams) {
  const categoryParam = categories.length > 0 ? categories.join(",") : "coffee";
  const merchantParam = merchantIds.length > 0 ? merchantIds.join(",") : "";

  return useInfiniteQuery({
    queryKey: ["products", "search", q, categoryParam, merchantParam, sort],
    queryFn: async ({ pageParam }) => {
      const params = new URLSearchParams();
      params.set("category", categoryParam);
      params.set("limit", "24");
      params.set("sort", sort);
      if (q) params.set("q", q);
      if (merchantParam) params.set("merchant_id", merchantParam);
      if (pageParam !== null && pageParam !== undefined) {
        params.set("cursor", String(pageParam));
      }
      const response = await fetch(`/api/v1/products/search?${params.toString()}`);
      if (!response.ok) throw new Error("Search failed");
      return response.json() as Promise<CursorPageProductSummary>;
    },
    initialPageParam: null as number | null,
    getNextPageParam: (lastPage) =>
      lastPage.has_more ? lastPage.next_cursor ?? undefined : undefined,
    staleTime: 30_000,
  });
}

export function useProductMerchantOptions(q: string, categories: string[] = ["coffee"]) {
  const categoryParam = categories.length > 0 ? categories.join(",") : "coffee";

  return useQuery({
    queryKey: ["products", "merchant-options", q, categoryParam],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.set("category", categoryParam);
      if (q) params.set("q", q);
      const response = await fetch(`/api/v1/products/merchant-options?${params.toString()}`);
      if (!response.ok) throw new Error("Merchant options fetch failed");
      return response.json() as Promise<ProductMerchantOption[]>;
    },
    staleTime: 60_000,
  });
}

export function useProduct(id: number | null) {
  return useQuery({
    queryKey: ["products", id],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/products/{product_id}", {
        params: { path: { product_id: id! } },
      });
      if (error) throw error;
      return data as ProductDetail;
    },
    enabled: !!id && id > 0,
    staleTime: 60_000,
  });
}

export function useProductOfferHistory(id: number | null, limit = 200) {
  return useQuery({
    queryKey: ["products", id, "offers", limit],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/products/{product_id}/offers", {
        params: {
          path: { product_id: id! },
          query: { limit },
        },
      });
      if (error) throw error;
      return data as OfferSnapshotSchema[];
    },
    enabled: !!id && id > 0,
    staleTime: 60_000,
  });
}
