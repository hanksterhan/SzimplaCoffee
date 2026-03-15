import { useState, useEffect } from "react";
import { Outlet } from "@tanstack/react-router";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { CommandPalette } from "./CommandPalette";
import { ErrorBoundary } from "@/components/ErrorBoundary";

export function AppShell() {
  const [cmdOpen, setCmdOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(
    () => localStorage.getItem("sidebar-collapsed") === "true"
  );
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Persist sidebar state
  useEffect(() => {
    localStorage.setItem("sidebar-collapsed", String(collapsed));
  }, [collapsed]);

  // ⌘K / Ctrl+K shortcut
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

  // Close mobile menu on resize to desktop
  useEffect(() => {
    const handler = () => {
      if (window.innerWidth >= 768) setMobileMenuOpen(false);
    };
    window.addEventListener("resize", handler);
    return () => window.removeEventListener("resize", handler);
  }, []);

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar
        collapsed={collapsed}
        mobileOpen={mobileMenuOpen}
        onMobileClose={() => setMobileMenuOpen(false)}
      />

      {/* Collapse toggle (desktop only) */}
      <button
        onClick={() => setCollapsed((v) => !v)}
        className="hidden md:flex absolute left-0 top-1/2 -translate-y-1/2 z-10 w-4 h-8 bg-[var(--coffee-americano)] text-white/60 hover:text-white items-center justify-center rounded-r text-xs transition-colors"
        aria-label="Toggle sidebar"
        style={{ left: collapsed ? "3.25rem" : "13.75rem" }}
      >
        {collapsed ? "›" : "‹"}
      </button>

      <div className="flex flex-col flex-1 min-w-0">
        <Topbar
          onCommandPaletteOpen={() => setCmdOpen(true)}
          onMobileMenuOpen={() => setMobileMenuOpen(true)}
        />
        <main className="flex-1 overflow-auto p-4 md:p-6">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>

      <CommandPalette open={cmdOpen} onClose={() => setCmdOpen(false)} />
    </div>
  );
}
