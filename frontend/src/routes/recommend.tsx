import { createFileRoute } from "@tanstack/react-router";

interface RecommendSearch {
  selectedRunId?: number;
}

export const Route = createFileRoute("/recommend")({
  validateSearch: (search: Record<string, unknown>): RecommendSearch => ({
    selectedRunId:
      typeof search.selectedRunId === "number"
        ? search.selectedRunId
        : typeof search.selectedRunId === "string" && search.selectedRunId.trim() !== ""
          ? Number(search.selectedRunId)
          : undefined,
  }),
  // Component is in recommend.lazy.tsx (code-split)
});
