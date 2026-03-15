import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

export interface CrawlScheduleItem {
  merchant_id: number;
  name: string;
  crawl_tier: string;
  interval_hours: number | null;
  last_crawl_at: string | null;
  next_due_at: string | null;
  is_due: boolean;
  status: string;
}

export interface RunDueResponse {
  triggered: number;
  merchant_ids: number[];
}

async function fetchDueMerchants(): Promise<CrawlScheduleItem[]> {
  const res = await fetch("/api/v1/crawl/due");
  if (!res.ok) throw new Error("Failed to fetch due merchants");
  return res.json() as Promise<CrawlScheduleItem[]>;
}

async function runDueCrawls(): Promise<RunDueResponse> {
  const res = await fetch("/api/v1/crawl/run-due", { method: "POST" });
  if (!res.ok) throw new Error("Failed to trigger crawls");
  return res.json() as Promise<RunDueResponse>;
}

export function useCrawlDue() {
  return useQuery({
    queryKey: ["crawl", "due"],
    queryFn: fetchDueMerchants,
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
}

export function useRunDueCrawls() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: runDueCrawls,
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: ["crawl"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success(`Crawl started for ${data.triggered} merchant${data.triggered !== 1 ? "s" : ""}`);
    },
    onError: (err: Error) => {
      toast.error(`Something went wrong: ${err.message}`);
    },
  });
}
