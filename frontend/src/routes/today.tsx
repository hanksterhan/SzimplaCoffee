import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/today")({
  // Component is in today.lazy.tsx (code-split)
});
