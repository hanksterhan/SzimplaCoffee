# SC-25 Execution Plan: Recommendation Console

## `frontend/src/hooks/useRecommendations.ts`
```typescript
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";

interface RecommendationRequest {
  shot_style: "espresso" | "filter" | "omni";
  bag_size_grams: 340 | 2268;
  budget_cents?: number;
  trust_tier_filter?: "trusted" | null;
}

export function useRecommendations() {
  return useQuery({
    queryKey: ["recommendations"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/recommendations");
      if (error) throw error;
      return data;
    },
    staleTime: 60_000,
  });
}

export function useCreateRecommendation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (req: RecommendationRequest) => {
      const { data, error } = await api.POST("/api/v1/recommendations", { body: req });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["recommendations"] });
    },
  });
}
```

## `frontend/src/components/recommendations/RecommendationForm.tsx`
```tsx
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";

interface FormProps {
  onSubmit: (req: { shot_style: string; bag_size_grams: number; budget_cents?: number; trust_tier_filter?: string }) => void;
  isLoading: boolean;
}

export function RecommendationForm({ onSubmit, isLoading }: FormProps) {
  const [shotStyle, setShotStyle] = useState("espresso");
  const [bagSize, setBagSize] = useState(340);
  const [budget, setBudget] = useState("");
  const [trustedOnly, setTrustedOnly] = useState(false);

  return (
    <Card>
      <CardHeader><CardTitle>☕ Get Recommendations</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium">Shot Style</label>
            <Select value={shotStyle} onValueChange={setShotStyle}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="espresso">Espresso</SelectItem>
                <SelectItem value="filter">Filter / Pour-Over</SelectItem>
                <SelectItem value="omni">Omni (Both)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm font-medium">Bag Size</label>
            <Select value={String(bagSize)} onValueChange={(v) => setBagSize(Number(v))}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="340">340g (12 oz)</SelectItem>
                <SelectItem value="2268">2268g (5 lb)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <div>
          <label className="text-sm font-medium">Max Budget (optional)</label>
          <Input
            type="number"
            placeholder="e.g. 25"
            value={budget}
            onChange={(e) => setBudget(e.target.value)}
          />
          <p className="text-xs text-muted-foreground mt-1">In dollars</p>
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={trustedOnly} onChange={(e) => setTrustedOnly(e.target.checked)} />
          Trusted merchants only (Olympia Coffee, Camber Coffee)
        </label>
        <Button
          onClick={() => onSubmit({
            shot_style: shotStyle,
            bag_size_grams: bagSize,
            budget_cents: budget ? Math.round(parseFloat(budget) * 100) : undefined,
            trust_tier_filter: trustedOnly ? "trusted" : undefined,
          })}
          disabled={isLoading}
          className="w-full"
        >
          {isLoading ? "Finding best coffee..." : "🎯 Get Recommendations"}
        </Button>
      </CardContent>
    </Card>
  );
}
```

## `frontend/src/components/recommendations/ResultCard.tsx`
```tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface ResultCardProps {
  result: {
    product_name?: string;
    merchant_name?: string;
    price_cents?: number;
    score?: number;
    rationale?: string;
    is_trusted?: boolean;
  };
  rank?: number;
}

export function ResultCard({ result, rank = 1 }: ResultCardProps) {
  const price = result.price_cents ? `$${(result.price_cents / 100).toFixed(2)}` : "--";
  const score = result.score ? `${Math.round(result.score * 100)}%` : "--";

  return (
    <Card className={rank === 1 ? "border-2 border-[var(--coffee-latte)]" : ""}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">
            {rank === 1 ? "⭐ " : `${rank}. `}{result.product_name ?? "Coffee"}
          </CardTitle>
          <div className="flex gap-2">
            {result.is_trusted && <Badge className="bg-green-100 text-green-700 text-xs">Trusted</Badge>}
            <Badge variant="outline">{score} match</Badge>
          </div>
        </div>
        <p className="text-sm text-muted-foreground">{result.merchant_name}</p>
      </CardHeader>
      <CardContent>
        <p className="text-xl font-bold">{price}</p>
        {result.rationale && (
          <p className="text-sm text-muted-foreground mt-2">{result.rationale}</p>
        )}
      </CardContent>
    </Card>
  );
}
```

## Main Route: `frontend/src/routes/recommendations.tsx`
```tsx
// Import RecommendationForm, ResultCard, RecommendationHistory
// State: activeResult (from latest mutation)
// Layout: form on left, result on right (or stacked on small)
// History below the form
```
