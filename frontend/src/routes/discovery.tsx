import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/discovery")({
  component: () => (
    <div className="p-8">
      <h1 className="text-3xl font-bold">Discovery</h1>
      <p className="mt-2 text-gray-600">Discover new coffee sources</p>
    </div>
  ),
});
