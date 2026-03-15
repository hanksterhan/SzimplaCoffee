import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import type { components } from "@/api/schema";

export type DashboardMetrics = components["schemas"]["DashboardMetrics"] & {
  /** SC-33: Number of merchants due for a crawl based on tier schedule */
  merchants_due_for_crawl?: number;
};

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard", "metrics"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/dashboard/metrics");
      if (error) throw error;
      return data as DashboardMetrics;
    },
    staleTime: 30_000,
    refetchInterval: 30_000,
  });
}
