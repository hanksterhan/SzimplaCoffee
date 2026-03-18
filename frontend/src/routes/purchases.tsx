import { createFileRoute } from "@tanstack/react-router";

interface PurchasesSearch {
  recommendationRunId?: number;
}

export const Route = createFileRoute("/purchases")({
  validateSearch: (search: Record<string, unknown>): PurchasesSearch => ({
    recommendationRunId:
      typeof search.recommendationRunId === "number"
        ? search.recommendationRunId
        : typeof search.recommendationRunId === "string" && search.recommendationRunId.trim() !== ""
          ? Number(search.recommendationRunId)
          : undefined,
  }),
  // Component is in purchases.lazy.tsx (code-split)
});
