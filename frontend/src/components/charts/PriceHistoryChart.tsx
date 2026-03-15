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

interface OfferPoint {
  id: number;
  observed_at: string;
  price_cents: number;
  compare_at_price_cents: number | null;
  is_on_sale: boolean;
  is_available: boolean;
  label?: string;
  variant_id?: number;
}

interface VariantHistory {
  variantId: number;
  label: string;
  offers: OfferPoint[];
}

interface PriceHistoryChartProps {
  variants: VariantHistory[];
  height?: number;
}

const COFFEE_COLORS = [
  "#2C1810", // espresso
  "#6B3A2A", // dark roast
  "#C8A882", // latte
  "#8B5E3C", // medium roast
  "#4A2C1A", // americano
  "#D4A96A", // caramel
  "#7A4530", // mahogany
];

const SALE_COLOR = "#E05C2A"; // burnt orange for sale markers

type ChartDataPoint = Record<string, number | string | null>;

function buildChartData(variants: VariantHistory[]): ChartDataPoint[] {
  const timeMap = new Map<string, ChartDataPoint>();

  variants.forEach(({ label, offers }) => {
    offers.forEach((offer) => {
      const date = new Date(offer.observed_at);
      const dateKey = date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
      if (!timeMap.has(dateKey)) {
        timeMap.set(dateKey, { date: dateKey, _ts: date.getTime() });
      }
      const entry = timeMap.get(dateKey)!;
      entry[label] = offer.price_cents / 100;
      entry[`${label}_sale`] = offer.is_on_sale ? 1 : 0;
    });
  });

  return Array.from(timeMap.values()).sort((a, b) => (a._ts as number) - (b._ts as number));
}

const formatPrice = (value: number) => `$${value.toFixed(2)}`;

interface CustomDotProps {
  cx?: number;
  cy?: number;
  payload?: ChartDataPoint;
  dataKey?: string;
}

function SaleDot({ cx, cy, payload, dataKey }: CustomDotProps) {
  if (!cx || !cy || !payload || !dataKey) return null;
  const label = dataKey as string;
  const isSale = payload[`${label}_sale`] === 1;
  if (isSale) {
    return <circle cx={cx} cy={cy} r={5} fill={SALE_COLOR} stroke="#fff" strokeWidth={1.5} />;
  }
  return null;
}

export function PriceHistoryChart({ variants, height = 300 }: PriceHistoryChartProps) {
  const activeVariants = variants.filter((v) => v.offers.length > 0);

  if (activeVariants.length === 0) {
    return (
      <div className="flex items-center justify-center text-muted-foreground text-sm py-8">
        No price history available
      </div>
    );
  }

  const data = buildChartData(activeVariants);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0e8e0" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11, fill: "#6b7280" }}
          tickLine={false}
        />
        <YAxis
          tickFormatter={formatPrice}
          tick={{ fontSize: 11, fill: "#6b7280" }}
          tickLine={false}
          axisLine={false}
          width={65}
        />
        <Tooltip
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          formatter={(value: any, name: any) => {
            const nameStr = String(name ?? "");
            if (nameStr.endsWith("_sale")) return [null, null];
            if (typeof value === "number") return [formatPrice(value), nameStr];
            return [String(value), nameStr];
          }}
          labelStyle={{ fontWeight: 600, color: "#2C1810" }}
          contentStyle={{
            border: "1px solid #e2d5c8",
            borderRadius: "8px",
            fontSize: "12px",
            backgroundColor: "#fffbf7",
          }}
          filterNull={true}
        />
        <Legend
          wrapperStyle={{ fontSize: "12px", paddingTop: "8px" }}
          formatter={(value: string) => (value.endsWith("_sale") ? null : value)}
        />
        {activeVariants.map(({ label }, i) => (
          <Line
            key={label}
            type="monotone"
            dataKey={label}
            stroke={COFFEE_COLORS[i % COFFEE_COLORS.length]}
            strokeWidth={2}
            dot={<SaleDot dataKey={label} />}
            activeDot={{ r: 5, strokeWidth: 1 }}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
