import { createFileRoute } from "@tanstack/react-router";

interface MerchantsSearch {
  platform_type?: string;
  trust_tier?: string;
}

export const Route = createFileRoute("/merchants")({
  validateSearch: (search: Record<string, unknown>): MerchantsSearch => ({
    platform_type:
      typeof search.platform_type === "string"
        ? search.platform_type
        : undefined,
    trust_tier:
      typeof search.trust_tier === "string" ? search.trust_tier : undefined,
  }),
  // Component is in merchants.lazy.tsx (code-split)
});
