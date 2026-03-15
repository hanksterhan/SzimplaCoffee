import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/products")({
  // Component is in products.lazy.tsx (code-split)
});
