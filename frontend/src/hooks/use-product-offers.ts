import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";

export interface ProductOfferPoint {
  id: number;
  observed_at: string;
  price_cents: number;
  compare_at_price_cents: number | null;
  subscription_price_cents: number | null;
  is_on_sale: boolean;
  is_available: boolean;
  source_url: string;
  price_dollars: number;
}

export function useProductOffers(productId: number | null, limit = 100) {
  return useQuery({
    queryKey: ["products", productId, "offers", limit],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/products/{product_id}/offers", {
        params: {
          path: { product_id: productId! },
          query: { limit },
        },
      });
      if (error) throw error;
      return data as ProductOfferPoint[];
    },
    enabled: !!productId && productId > 0,
    staleTime: 60_000,
  });
}

export function useProductDetail(productId: number | null) {
  return useQuery({
    queryKey: ["products", productId],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/products/{product_id}", {
        params: { path: { product_id: productId! } },
      });
      if (error) throw error;
      return data;
    },
    enabled: !!productId && productId > 0,
    staleTime: 60_000,
  });
}
