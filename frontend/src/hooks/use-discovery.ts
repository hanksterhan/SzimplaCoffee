import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import type { components } from "@/api/schema";

export type MerchantCandidateSchema =
  components["schemas"]["MerchantCandidateSchema"];

export function useDiscoveryCandidates(status?: string) {
  return useQuery({
    queryKey: ["discovery", "candidates", status ?? "pending"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/discovery/candidates", {
        params: { query: { status: status ?? "pending" } },
      });
      if (error) throw error;
      return data as MerchantCandidateSchema[];
    },
    staleTime: 30_000,
  });
}

export function useRunDiscovery() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (query?: string) => {
      const q = query ?? "specialty coffee roaster";
      const { data, error } = await api.POST("/api/v1/discovery/run", {
        params: { query: { query: q } },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      setTimeout(() => qc.invalidateQueries({ queryKey: ["discovery"] }), 4000);
    },
  });
}

export function usePromoteCandidate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (candidateId: number) => {
      const { data, error } = await api.POST(
        "/api/v1/discovery/candidates/{candidate_id}/promote",
        { params: { path: { candidate_id: candidateId } } }
      );
      if (error) throw error;
      return data as { status: string; merchant_id: number; note?: string };
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["discovery"] });
      qc.invalidateQueries({ queryKey: ["merchants"] });
    },
  });
}

export function useRejectCandidate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (candidateId: number) => {
      const { data, error } = await api.POST(
        "/api/v1/discovery/candidates/{candidate_id}/reject",
        { params: { path: { candidate_id: candidateId } } }
      );
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["discovery"] });
    },
  });
}
