import { Link } from "@tanstack/react-router";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";

const NAV_ITEMS: Array<{ to: string; label: string; icon: string }> = [
  { to: "/", label: "Dashboard", icon: "☕" },
  { to: "/today", label: "Today", icon: "🗓️" },
  { to: "/merchants", label: "Merchants", icon: "🏪" },
  { to: "/products", label: "Products", icon: "📦" },
  { to: "/recommend", label: "Recommendations", icon: "🎯" },
  { to: "/discovery", label: "Discovery", icon: "🔍" },
  { to: "/watch", label: "Watch & Review", icon: "👁️" },
  { to: "/purchases", label: "Purchases", icon: "🛒" },
];

interface SidebarProps {
  collapsed?: boolean;
  /** Mobile: whether the sheet overlay is open */
  mobileOpen?: boolean;
  onMobileClose?: () => void;
}

export function Sidebar({ collapsed = false, mobileOpen = false, onMobileClose }: SidebarProps) {
  const navContent = (
    <>
      {/* Logo */}
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        {collapsed ? (
          <span className="text-xl">☕</span>
        ) : (
          <span className="font-bold text-lg tracking-tight">SzimplaCoffee</span>
        )}
        {/* Mobile close button */}
        {mobileOpen && onMobileClose && (
          <button
            onClick={onMobileClose}
            className="ml-auto text-[var(--coffee-cream)]/60 hover:text-[var(--coffee-cream)] md:hidden"
            aria-label="Close menu"
          >
            <X size={20} />
          </button>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 p-2 space-y-1">
        {NAV_ITEMS.map(({ to, label, icon }) => (
          <Link
            key={to}
            to={to}
            onClick={onMobileClose}
            className="flex items-center gap-3 px-3 py-2 rounded-md text-sm hover:bg-white/10 transition-colors text-[var(--coffee-cream)]/80 hover:text-[var(--coffee-cream)]"
            activeProps={{ className: "bg-white/20 font-medium text-[var(--coffee-cream)]" }}
          >
            <span className="text-base">{icon}</span>
            {!collapsed && <span>{label}</span>}
          </Link>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-white/10 text-xs text-[var(--coffee-cream)]/40">
        {!collapsed && "SzimplaCoffee v0.1"}
      </div>
    </>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside
        className={cn(
          "hidden md:flex flex-col h-full bg-[var(--coffee-espresso)] text-[var(--coffee-cream)] transition-all duration-200",
          collapsed ? "w-14" : "w-56"
        )}
      >
        {navContent}
      </aside>

      {/* Mobile overlay */}
      {mobileOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/50 z-40 md:hidden"
            onClick={onMobileClose}
            aria-hidden="true"
          />
          {/* Drawer */}
          <aside className="fixed left-0 top-0 h-full w-64 z-50 flex flex-col bg-[var(--coffee-espresso)] text-[var(--coffee-cream)] md:hidden shadow-xl">
            {navContent}
          </aside>
        </>
      )}
    </>
  );
}
