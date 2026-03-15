# SC-20 Execution Plan: App Shell — Sidebar, Layout, Command Palette

## `frontend/src/components/layout/Sidebar.tsx`
```tsx
import { Link } from "@tanstack/react-router";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: "☕" },
  { to: "/merchants", label: "Merchants", icon: "🏪" },
  { to: "/products", label: "Products", icon: "📦" },
  { to: "/recommendations", label: "Recommendations", icon: "🎯" },
  { to: "/discovery", label: "Discovery", icon: "🔍" },
] as const;

export function Sidebar({ collapsed = false }: { collapsed?: boolean }) {
  return (
    <aside
      className={cn(
        "flex flex-col h-full bg-[var(--coffee-espresso)] text-[var(--coffee-cream)]",
        collapsed ? "w-14" : "w-56"
      )}
    >
      {/* Logo */}
      <div className="p-4 border-b border-white/10">
        {collapsed ? "☕" : <span className="font-bold text-lg">SzimplaCoffee</span>}
      </div>

      {/* Nav */}
      <nav className="flex-1 p-2 space-y-1">
        {NAV_ITEMS.map(({ to, label, icon }) => (
          <Link
            key={to}
            to={to}
            className="flex items-center gap-3 px-3 py-2 rounded-md text-sm hover:bg-white/10 transition-colors"
            activeProps={{ className: "bg-white/20 font-medium" }}
          >
            <span>{icon}</span>
            {!collapsed && <span>{label}</span>}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
```

## `frontend/src/components/layout/Topbar.tsx`
```tsx
import { Button } from "@/components/ui/button";
import { Search } from "lucide-react";

interface TopbarProps {
  onCommandPaletteOpen: () => void;
}

export function Topbar({ onCommandPaletteOpen }: TopbarProps) {
  return (
    <header className="h-12 border-b flex items-center px-4 gap-4 bg-card">
      <Button
        variant="outline"
        size="sm"
        className="flex items-center gap-2 text-muted-foreground"
        onClick={onCommandPaletteOpen}
      >
        <Search size={14} />
        <span>Search...</span>
        <kbd className="text-xs bg-muted px-1.5 rounded">⌘K</kbd>
      </Button>
    </header>
  );
}
```

## `frontend/src/components/layout/CommandPalette.tsx`
```tsx
import { useEffect, useState } from "react";
import { Command } from "cmdk";
import { useNavigate } from "@tanstack/react-router";
import { Dialog, DialogContent } from "@/components/ui/dialog";

const COMMANDS = [
  { label: "Dashboard", to: "/", group: "Navigate" },
  { label: "Merchants", to: "/merchants", group: "Navigate" },
  { label: "Products", to: "/products", group: "Navigate" },
  { label: "Recommendations", to: "/recommendations", group: "Navigate" },
  { label: "Discovery", to: "/discovery", group: "Navigate" },
  { label: "Add Merchant", to: "/merchants/new", group: "Actions" },
  { label: "Run Recommendations", to: "/recommendations/new", group: "Actions" },
];

export function CommandPalette({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const navigate = useNavigate();

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="p-0 max-w-lg">
        <Command>
          <Command.Input placeholder="Type a command or search..." className="border-0" />
          <Command.List className="max-h-80 overflow-y-auto p-2">
            <Command.Empty>No results found.</Command.Empty>
            {["Navigate", "Actions"].map((group) => (
              <Command.Group heading={group} key={group}>
                {COMMANDS.filter((c) => c.group === group).map((cmd) => (
                  <Command.Item
                    key={cmd.to}
                    onSelect={() => {
                      navigate({ to: cmd.to });
                      onClose();
                    }}
                    className="cursor-pointer"
                  >
                    {cmd.label}
                  </Command.Item>
                ))}
              </Command.Group>
            ))}
          </Command.List>
        </Command>
      </DialogContent>
    </Dialog>
  );
}
```

## `frontend/src/components/layout/AppShell.tsx`
```tsx
import { useState, useEffect } from "react";
import { Outlet } from "@tanstack/react-router";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { CommandPalette } from "./CommandPalette";

export function AppShell() {
  const [cmdOpen, setCmdOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(
    () => localStorage.getItem("sidebar-collapsed") === "true"
  );

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setCmdOpen((v) => !v);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar collapsed={collapsed} />
      <div className="flex flex-col flex-1 min-w-0">
        <Topbar onCommandPaletteOpen={() => setCmdOpen(true)} />
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
      <CommandPalette open={cmdOpen} onClose={() => setCmdOpen(false)} />
    </div>
  );
}
```

## Update `__root.tsx`
```tsx
import { AppShell } from "@/components/layout/AppShell";

export const Route = createRootRouteWithContext<RouterContext>()({
  component: AppShell,
});
```

## Install cmdk
```bash
cd frontend && npm install cmdk lucide-react
```
