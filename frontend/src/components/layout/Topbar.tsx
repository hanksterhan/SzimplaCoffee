import { Button } from "@/components/ui/button";
import { Search, Menu } from "lucide-react";

interface TopbarProps {
  onCommandPaletteOpen: () => void;
  onMobileMenuOpen?: () => void;
}

export function Topbar({ onCommandPaletteOpen, onMobileMenuOpen }: TopbarProps) {
  return (
    <header className="h-12 border-b flex items-center px-4 gap-4 bg-card shrink-0">
      {/* Hamburger — mobile only */}
      {onMobileMenuOpen && (
        <button
          onClick={onMobileMenuOpen}
          className="md:hidden text-muted-foreground hover:text-foreground p-1 -ml-1"
          aria-label="Open menu"
        >
          <Menu size={20} />
        </button>
      )}

      <Button
        variant="outline"
        size="sm"
        className="flex items-center gap-2 text-muted-foreground w-full sm:w-64 justify-start"
        onClick={onCommandPaletteOpen}
      >
        <Search size={14} />
        <span className="flex-1 text-left">Search...</span>
        <kbd className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono hidden sm:inline">⌘K</kbd>
      </Button>
    </header>
  );
}
