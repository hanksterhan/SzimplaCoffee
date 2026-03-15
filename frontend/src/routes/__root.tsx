import { createRootRouteWithContext } from "@tanstack/react-router";
import { QueryClient } from "@tanstack/react-query";
import { AppShell } from "@/components/layout/AppShell";
import { Toaster } from "@/components/ui/toaster";

interface RouterContext {
  queryClient: QueryClient;
}

function RootComponent() {
  return (
    <>
      <AppShell />
      <Toaster />
    </>
  );
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: RootComponent,
});
