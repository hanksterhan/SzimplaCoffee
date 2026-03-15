import { useQuery, useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { components } from "@/api/schema";

export type CursorPageProductSummary = components["schemas"]["CursorPage_ProductSummary_"];
import { toast } from "sonner";
import { api } from "@/api/client";

interface MerchantsFilter {
  platform_type?: string;
  trust_tier?: string;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}

export function useMerchants(filters: MerchantsFilter = {}) {
  return useQuery({
    queryKey: ["merchants", filters],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/merchants", {
        params: {
          query: {
            platform_type: filters.platform_type,
            trust_tier: filters.trust_tier,
            is_active: filters.is_active,
            page: filters.page ?? 1,
            page_size: filters.page_size ?? 25,
          },
        },
      });
      if (error) throw error;
      return data;
    },
    staleTime: 30_000,
  });
}

export function useMerchant(id: number) {
  return useQuery({
    queryKey: ["merchants", id],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/merchants/{merchant_id}", {
        params: { path: { merchant_id: id } },
      });
      if (error) throw error;
      return data;
    },
    enabled: !!id && id > 0,
  });
}

export function useMerchantProducts(merchantId: number, category = "coffee") {
  return useInfiniteQuery({
    queryKey: ["merchants", merchantId, "products", category],
    queryFn: async ({ pageParam }) => {
      const response = await fetch(
        `/api/v1/merchants/${merchantId}/products?category=${encodeURIComponent(category || "coffee")}&limit=24${pageParam ? `&cursor=${pageParam}` : ""}`
      );
      if (!response.ok) throw new Error("Failed to fetch products");
      return response.json() as Promise<CursorPageProductSummary>;
    },
    initialPageParam: null as number | null,
    getNextPageParam: (lastPage) =>
      lastPage.has_more ? lastPage.next_cursor ?? undefined : undefined,
    enabled: !!merchantId && merchantId > 0,
    staleTime: 30_000,
  });
}

export function useMerchantCrawlRuns(merchantId: number) {
  return useQuery({
    queryKey: ["merchants", merchantId, "crawl-runs"],
    queryFn: async () => {
      const { data, error } = await api.GET(
        "/api/v1/merchants/{merchant_id}/crawl-runs",
        {
          params: { path: { merchant_id: merchantId } },
        }
      );
      if (error) throw error;
      return data;
    },
    enabled: !!merchantId && merchantId > 0,
  });
}

export function useMerchantPromos(merchantId: number) {
  return useQuery({
    queryKey: ["merchants", merchantId, "promos"],
    queryFn: async () => {
      const { data, error } = await api.GET(
        "/api/v1/merchants/{merchant_id}/promos",
        {
          params: { path: { merchant_id: merchantId } },
        }
      );
      if (error) throw error;
      return data;
    },
    enabled: !!merchantId && merchantId > 0,
  });
}

export function useMerchantStatus(merchantId: number) {
  return useQuery({
    queryKey: ["merchants", merchantId, "status"],
    queryFn: async () => {
      const { data, error } = await api.GET(
        "/api/v1/merchants/{merchant_id}/status",
        {
          params: { path: { merchant_id: merchantId } },
        }
      );
      if (error) throw error;
      return data;
    },
    enabled: !!merchantId && merchantId > 0,
    refetchInterval: 5_000,
  });
}

export function useAddMerchant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { url: string; trust_tier?: string }) => {
      const { data, error } = await api.POST("/api/v1/merchants", {
        body: {
          url: payload.url,
          trust_tier: payload.trust_tier ?? "candidate",
        },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["merchants"] });
      toast.success("Merchant added successfully");
    },
    onError: (err: Error) => {
      toast.error(`Something went wrong: ${err.message}`);
    },
  });
}

export function useTriggerCrawl() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ merchantId, merchantName }: { merchantId: number; merchantName?: string }) => {
      const { data, error } = await api.POST(
        "/api/v1/merchants/{merchant_id}/crawl",
        {
          params: { path: { merchant_id: merchantId } },
        }
      );
      if (error) throw error;
      return { data, merchantName };
    },
    onSuccess: ({ merchantName }, { merchantId }) => {
      qc.invalidateQueries({ queryKey: ["merchants"] });
      qc.invalidateQueries({ queryKey: ["merchants", merchantId, "crawl-runs"] });
      qc.invalidateQueries({ queryKey: ["merchants", merchantId, "status"] });
      toast.success(`Crawl started${merchantName ? ` for ${merchantName}` : ""}`);
    },
    onError: (err: Error) => {
      toast.error(`Something went wrong: ${err.message}`);
    },
  });
}
