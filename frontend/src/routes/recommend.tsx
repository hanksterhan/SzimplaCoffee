import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/recommend")({
  component: () => (
    <div className="p-8">
      <h1 className="text-3xl font-bold">Recommendations</h1>
      <p className="mt-2 text-gray-600">AI-powered coffee recommendations</p>
    </div>
  ),
});
