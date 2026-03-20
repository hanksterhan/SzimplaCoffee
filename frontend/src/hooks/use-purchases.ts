import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/api/client";
import type { components } from "@/api/schema";

export type PurchaseSummary = components["schemas"]["PurchaseSummary"] & {
  recommendation_run_id?: number | null;
};
export type PurchaseDetail = components["schemas"]["PurchaseDetail"] & {
  recommendation_run_id?: number | null;
};
export type PurchaseCreate = components["schemas"]["PurchaseCreate"] & {
  recommendation_run_id?: number | null;
};
export type PurchaseUpdate = components["schemas"]["PurchaseUpdate"] & {
  recommendation_run_id?: number | null;
};
export type PurchaseStats = components["schemas"]["PurchaseStats"];
export type BuyingPatternStats = components["schemas"]["BuyingPatternStats"];
export type TopRoaster = components["schemas"]["TopRoaster"];

interface PurchasesFilter {
  merchant_id?: number;
  date_from?: string;
  date_to?: string;
}

export function usePurchases(filters: PurchasesFilter = {}) {
  return useQuery({
    queryKey: ["purchases", filters],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/purchases", {
        params: {
          query: {
            merchant_id: filters.merchant_id,
            date_from: filters.date_from,
            date_to: filters.date_to,
          },
        },
      });
      if (error) throw error;
      return data as PurchaseSummary[];
    },
    staleTime: 30_000,
  });
}

export function usePurchase(id: number) {
  return useQuery({
    queryKey: ["purchases", id],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/purchases/{purchase_id}", {
        params: { path: { purchase_id: id } },
      });
      if (error) throw error;
      return data as PurchaseDetail;
    },
    enabled: id > 0,
  });
}

export function usePurchaseStats() {
  return useQuery({
    queryKey: ["purchases", "stats"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/purchases/stats");
      if (error) throw error;
      return data as PurchaseStats;
    },
    staleTime: 60_000,
  });
}

export function useAddPurchase() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: PurchaseCreate) => {
      const { data, error } = await api.POST("/api/v1/purchases", { body });
      if (error) throw error;
      return data as PurchaseDetail;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["purchases"] });
      toast.success("Purchase logged");
    },
    onError: (err: Error) => {
      toast.error(`Something went wrong: ${err.message}`);
    },
  });
}

export function useUpdatePurchase() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, body }: { id: number; body: PurchaseUpdate }) => {
      const { data, error } = await api.PUT("/api/v1/purchases/{purchase_id}", {
        params: { path: { purchase_id: id } },
        body,
      });
      if (error) throw error;
      return data as PurchaseDetail;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["purchases"] });
      toast.success("Purchase updated");
    },
    onError: (err: Error) => {
      toast.error(`Something went wrong: ${err.message}`);
    },
  });
}

export function useDeletePurchase() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { error } = await api.DELETE("/api/v1/purchases/{purchase_id}", {
        params: { path: { purchase_id: id } },
      });
      if (error) throw error;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["purchases"] });
      toast.success("Deleted successfully");
    },
    onError: (err: Error) => {
      toast.error(`Something went wrong: ${err.message}`);
    },
  });
}

export function useBuyingPatterns() {
  return useQuery({
    queryKey: ["purchases", "buying-patterns"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/history/purchase-stats");
      if (error) throw error;
      return data as BuyingPatternStats;
    },
    staleTime: 60_000,
  });
}
