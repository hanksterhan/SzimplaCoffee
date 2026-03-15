import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/merchants/$merchantId")({
  // Component is in merchants.$merchantId.lazy.tsx (code-split)
});
