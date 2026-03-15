import { Toaster as Sonner } from "sonner";

export function Toaster() {
  return (
    <Sonner
      position="bottom-right"
      toastOptions={{
        style: {
          background: "hsl(var(--background))",
          border: "1px solid hsl(var(--border))",
          color: "hsl(var(--foreground))",
        },
      }}
    />
  );
}
