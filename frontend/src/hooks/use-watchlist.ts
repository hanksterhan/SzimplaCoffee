import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { components } from "@/api/schema";

export type MerchantSummary = components["schemas"]["MerchantSummary"];

export function useWatchlist() {
  return useQuery({
    queryKey: ["merchants", "watchlist"],
    queryFn: async () => {
      const response = await fetch("/api/v1/merchants/watchlist");
      if (!response.ok) throw new Error("Failed to fetch watchlist");
      return response.json() as Promise<MerchantSummary[]>;
    },
    staleTime: 60_000,
  });
}

export function useAddToWatchlist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (merchantId: number) => {
      const response = await fetch(`/api/v1/merchants/${merchantId}/watch`, {
        method: "POST",
      });
      if (!response.ok) throw new Error("Failed to add to watchlist");
      return response.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["merchants"] });
    },
  });
}

export function useRemoveFromWatchlist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (merchantId: number) => {
      const response = await fetch(`/api/v1/merchants/${merchantId}/watch`, {
        method: "DELETE",
      });
      if (!response.ok) throw new Error("Failed to remove from watchlist");
      return response.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["merchants"] });
    },
  });
}

export function useLowConfidenceMerchants(maxQualityScore = 0.5) {
  return useQuery({
    queryKey: ["merchants", "low-confidence", maxQualityScore],
    queryFn: async () => {
      const response = await fetch(
        `/api/v1/merchants/low-confidence?max_quality_score=${maxQualityScore}`
      );
      if (!response.ok) throw new Error("Failed to fetch low-confidence merchants");
      return response.json() as Promise<MerchantSummary[]>;
    },
    staleTime: 5 * 60_000,
  });
}
