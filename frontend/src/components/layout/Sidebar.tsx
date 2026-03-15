import { Link } from "@tanstack/react-router";
import { cn } from "@/lib/utils";

const NAV_ITEMS: Array<{ to: string; label: string; icon: string }> = [
  { to: "/", label: "Dashboard", icon: "☕" },
  { to: "/merchants", label: "Merchants", icon: "🏪" },
  { to: "/recommend", label: "Recommendations", icon: "🎯" },
  { to: "/discovery", label: "Discovery", icon: "🔍" },
  { to: "/purchases", label: "Purchases", icon: "🛒" },
];

export function Sidebar({ collapsed = false }: { collapsed?: boolean }) {
  return (
    <aside
      className={cn(
        "flex flex-col h-full bg-[var(--coffee-espresso)] text-[var(--coffee-cream)] transition-all duration-200",
        collapsed ? "w-14" : "w-56"
      )}
    >
      {/* Logo */}
      <div className="p-4 border-b border-white/10 flex items-center">
        {collapsed ? (
          <span className="text-xl">☕</span>
        ) : (
          <span className="font-bold text-lg tracking-tight">SzimplaCoffee</span>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 p-2 space-y-1">
        {NAV_ITEMS.map(({ to, label, icon }) => (
          <Link
            key={to}
            to={to}
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
    </aside>
  );
}
