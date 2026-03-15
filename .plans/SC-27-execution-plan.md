# SC-27 Execution Plan: Price History Chart (Recharts)

## Install
```bash
cd frontend && npm install recharts
# recharts ships its own types in newer versions
```

## `frontend/src/components/charts/PriceHistoryChart.tsx`
```tsx
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { OfferSnapshotSchema } from "@/api";

interface VariantHistory {
  variantId: number;
  label: string;
  offers: OfferSnapshotSchema[];
}

interface PriceHistoryChartProps {
  variants: VariantHistory[];
  height?: number;
}

const COLORS = [
  "#2C1810", // espresso
  "#C8A882", // latte
  "#6B3A2A", // roast
  "#4A2C1A", // americano
  "#8B5E3C", // medium
];

// Convert variant offer arrays into a unified time series
function buildChartData(variants: VariantHistory[]): Record<string, number | string>[] {
  const timeMap = new Map<string, Record<string, number | string>>();

  variants.forEach(({ variantId, label, offers }) => {
    offers.forEach((offer) => {
      const dateKey = new Date(offer.observed_at).toLocaleDateString();
      if (!timeMap.has(dateKey)) {
        timeMap.set(dateKey, { date: dateKey });
      }
      const entry = timeMap.get(dateKey)!;
      entry[label] = offer.price_cents / 100;
    });
  });

  return Array.from(timeMap.values()).sort((a, b) =>
    String(a.date).localeCompare(String(b.date))
  );
}

const formatPrice = (value: number) => `$${value.toFixed(2)}`;

export function PriceHistoryChart({ variants, height = 300 }: PriceHistoryChartProps) {
  if (variants.length === 0 || variants.every((v) => v.offers.length === 0)) {
    return (
      <div className="flex items-center justify-center h-32 text-muted-foreground text-sm">
        No price history available
      </div>
    );
  }

  const data = buildChartData(variants);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0e8e0" />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} />
        <YAxis tickFormatter={formatPrice} tick={{ fontSize: 12 }} width={70} />
        <Tooltip
          formatter={(value: number, name: string) => [formatPrice(value), name]}
          labelStyle={{ fontWeight: "bold" }}
          contentStyle={{ border: "1px solid #e2d5c8", borderRadius: "6px" }}
        />
        <Legend />
        {variants.map(({ label }, i) => (
          <Line
            key={label}
            type="monotone"
            dataKey={label}
            stroke={COLORS[i % COLORS.length]}
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
```

## Usage in ProductsTab (expandable row)
```tsx
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PriceHistoryChart } from "@/components/charts/PriceHistoryChart";

// When product row is expanded, load variant offer history
function ExpandedProductRow({ product }: { product: ProductSummary }) {
  const { data: detail } = useQuery({
    queryKey: ["products", product.id],
    queryFn: async () => {
      const { data } = await api.GET("/api/v1/products/{product_id}", {
        params: { path: { product_id: product.id } },
      });
      return data;
    },
  });

  const variants = detail?.variants?.map((v) => ({
    variantId: v.id,
    label: v.label,
    offers: v.offers ?? [],
  })) ?? [];

  return (
    <div className="p-4 bg-muted/20">
      <PriceHistoryChart variants={variants} height={200} />
    </div>
  );
}
```

## Note on Current Data
All 9352 offer snapshots are from 2026-03-09. The chart will show a single data point per variant (flat line). As the crawler runs daily, the chart will fill in over time. The component handles this gracefully with `connectNulls` and single-point dots.
