import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import type { components } from "@/api/schema";

export type ProductSummary = components["schemas"]["ProductSummary"];
export type ProductDetail = components["schemas"]["ProductDetail"];
export type ProductVariantSchema = components["schemas"]["ProductVariantSchema"];
export type OfferSnapshotSchema = components["schemas"]["OfferSnapshotSchema"];

export function useProductSearch(q: string, page = 1, pageSize = 24, category = "coffee") {
  return useQuery({
    queryKey: ["products", "search", q, page, pageSize, category],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/products/search", {
        params: {
          query: {
            q: q || undefined,
            page,
            page_size: pageSize,
            category: category || undefined,
          },
        },
      });
      if (error) throw error;
      return data;
    },
    staleTime: 30_000,
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
