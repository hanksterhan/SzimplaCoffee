import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/merchants")({
  component: () => (
    <div className="p-8">
      <h1 className="text-3xl font-bold">Merchants</h1>
      <p className="mt-2 text-gray-600">Browse coffee merchants</p>
    </div>
  ),
});
