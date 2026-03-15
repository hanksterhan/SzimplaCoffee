# SC-19 Execution Plan: shadcn/ui with Coffee Design Tokens

## Setup Commands
```bash
cd frontend

# shadcn/ui with Tailwind v4 support (canary)
npx shadcn@canary init

# Install core components
npx shadcn@canary add button card badge table input select dialog tabs skeleton separator dropdown-menu tooltip
```

## `frontend/components.json`
```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "src/index.css",
    "baseColor": "neutral",
    "cssVariables": true
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui"
  }
}
```

## Coffee Design Tokens (`frontend/src/index.css`)
```css
@import "tailwindcss";

/* Coffee Theme — warm palette */
:root {
  /* Core palette */
  --background: 30 20% 98%;          /* cream white */
  --foreground: 20 15% 10%;          /* dark roast text */

  --primary: 20 60% 25%;             /* espresso brown */
  --primary-foreground: 30 20% 98%;  /* cream on espresso */

  --secondary: 30 30% 90%;           /* latte foam */
  --secondary-foreground: 20 15% 20%;

  --muted: 30 15% 92%;               /* light steam */
  --muted-foreground: 20 10% 45%;

  --accent: 25 70% 35%;              /* roasted caramel */
  --accent-foreground: 30 20% 98%;

  --destructive: 0 60% 45%;
  --destructive-foreground: 0 0% 98%;

  --border: 30 20% 85%;              /* light brown border */
  --input: 30 20% 85%;
  --ring: 20 60% 25%;

  --card: 30 20% 98%;
  --card-foreground: 20 15% 10%;

  --popover: 30 20% 98%;
  --popover-foreground: 20 15% 10%;

  --radius: 0.5rem;

  /* Custom coffee tokens */
  --coffee-espresso: #2C1810;
  --coffee-americano: #4A2C1A;
  --coffee-latte: #C8A882;
  --coffee-cream: #FFF8F0;
  --coffee-steam: #F5F0EB;
  --coffee-roast: #6B3A2A;

  /* Status colors */
  --status-trusted: 142 50% 35%;     /* trusted = green */
  --status-candidate: 45 80% 45%;    /* candidate = amber */
  --status-pending: 200 60% 40%;     /* pending = blue */
  --status-rejected: 0 60% 45%;      /* rejected = red */
}
```

## `frontend/src/lib/utils.ts`
```typescript
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

## Badge Variants for Trust Tier
Add to `frontend/src/components/ui/trust-badge.tsx`:
```tsx
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type TrustTier = "trusted" | "verified" | "candidate" | "rejected";

const tierConfig: Record<TrustTier, { label: string; className: string }> = {
  trusted: { label: "Trusted", className: "bg-green-100 text-green-800 border-green-200" },
  verified: { label: "Verified", className: "bg-blue-100 text-blue-800 border-blue-200" },
  candidate: { label: "Candidate", className: "bg-amber-100 text-amber-800 border-amber-200" },
  rejected: { label: "Rejected", className: "bg-red-100 text-red-800 border-red-200" },
};

export function TrustBadge({ tier }: { tier: TrustTier }) {
  const { label, className } = tierConfig[tier] ?? tierConfig.candidate;
  return <Badge variant="outline" className={cn("text-xs", className)}>{label}</Badge>;
}
```

## `frontend/DESIGN.md`
Document color decisions, component usage patterns, and brand rationale.
