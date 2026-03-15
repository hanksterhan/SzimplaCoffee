import { useQuery } from "@tanstack/react-query";

export interface TodayRecommendationCandidate {
  merchant_name: string;
  product_name: string;
  variant_label: string;
  product_url: string;
  image_url: string;
  weight_grams: number | null;
  landed_price_cents: number;
  landed_price_per_oz_cents: number | null;
  best_promo_label: string | null;
  discounted_landed_price_cents: number | null;
  score: number;
  pros: string[];
}

export interface TodaySaleCandidate {
  merchant_name: string;
  product_name: string;
  variant_label: string;
  product_url: string;
  image_url: string;
  weight_grams: number | null;
  current_price_cents: number;
  landed_price_cents: number;
  landed_price_per_oz_cents: number | null;
  compare_at_discount_percent: number;
  price_drop_7d_percent: number;
  price_drop_30d_percent: number;
  historical_low_cents: number;
  best_promo_label: string | null;
  discounted_landed_price_cents: number | null;
  score: number;
  reasons: string[];
}

export interface TodayBriefResult {
  has_recommendation: boolean;
  top_pick: TodayRecommendationCandidate | null;
  alternatives: TodayRecommendationCandidate[];
  notable_sales: TodaySaleCandidate[];
  shot_style: string;
  quantity_mode: string;
  wait_recommendation: boolean;
}

export interface TodayBriefOptions {
  shot_style?: string;
  quantity_mode?: string;
  limit?: number;
}

export function useTodayBrief(options: TodayBriefOptions = {}) {
  const { shot_style = "modern_58mm", quantity_mode = "12-18 oz", limit = 5 } = options;

  return useQuery({
    queryKey: ["today", shot_style, quantity_mode, limit],
    queryFn: async () => {
      const params = new URLSearchParams({
        shot_style,
        quantity_mode,
        limit: String(limit),
      });
      const response = await fetch(`/api/v1/recommendations/today?${params}`);
      if (!response.ok) throw new Error("Failed to fetch today brief");
      return response.json() as Promise<TodayBriefResult>;
    },
    staleTime: 5 * 60_000, // 5 minutes
  });
}
