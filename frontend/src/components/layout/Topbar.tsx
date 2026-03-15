import { Button } from "@/components/ui/button";
import { Search } from "lucide-react";

interface TopbarProps {
  onCommandPaletteOpen: () => void;
}

export function Topbar({ onCommandPaletteOpen }: TopbarProps) {
  return (
    <header className="h-12 border-b flex items-center px-4 gap-4 bg-card shrink-0">
      <Button
        variant="outline"
        size="sm"
        className="flex items-center gap-2 text-muted-foreground w-64 justify-start"
        onClick={onCommandPaletteOpen}
      >
        <Search size={14} />
        <span className="flex-1 text-left">Search...</span>
        <kbd className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono">⌘K</kbd>
      </Button>
    </header>
  );
}
