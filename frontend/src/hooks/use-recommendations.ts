import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import type { components } from "@/api/schema";

export type RecommendationRequestPayload =
  components["schemas"]["RecommendationRequestPayload"];
export type RecommendationResultResponse =
  components["schemas"]["RecommendationResultResponse"];
export type RecommendationCandidateOut =
  components["schemas"]["RecommendationCandidateOut"];
export type RecommendationRunSchema =
  components["schemas"]["RecommendationRunSchema"];

export function useRecommendations() {
  return useQuery({
    queryKey: ["recommendations"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/recommendations");
      if (error) throw error;
      return data as RecommendationRunSchema[];
    },
    staleTime: 30_000,
  });
}

export function useRecommendation(runId: number) {
  return useQuery({
    queryKey: ["recommendations", runId],
    queryFn: async () => {
      const { data, error } = await api.GET(
        "/api/v1/recommendations/{run_id}",
        { params: { path: { run_id: runId } } }
      );
      if (error) throw error;
      return data as RecommendationRunSchema;
    },
    enabled: runId > 0,
  });
}

export function useRequestRecommendation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: RecommendationRequestPayload) => {
      const { data, error } = await api.POST("/api/v1/recommendations", {
        body: payload,
      });
      if (error) throw error;
      return data as RecommendationResultResponse;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["recommendations"] });
    },
  });
}
