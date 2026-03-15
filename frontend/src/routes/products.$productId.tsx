import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/products/$productId")({
  // Component is in products.$productId.lazy.tsx (code-split)
});
