import type { components } from "@/api/schema";

type MetadataFillRates = components["schemas"]["MetadataFillRates"];

interface MetadataFillRateWidgetProps {
  fillRates: MetadataFillRates | undefined;
}

interface FillRow {
  label: string;
  pct: number;
  showGoal?: boolean;
}

function colorClass(pct: number): string {
  if (pct >= 70) return "bg-green-500";
  if (pct >= 40) return "bg-amber-400";
  return "bg-red-400";
}

function textColorClass(pct: number): string {
  if (pct >= 70) return "text-green-600";
  if (pct >= 40) return "text-amber-600";
  return "text-red-500";
}

function FillRateRow({ label, pct, showGoal }: FillRow) {
  const displayPct = Math.min(pct, 100);
  const goalPct = 70;

  return (
    <div className="flex items-center gap-3">
      <span className="w-16 shrink-0 text-xs text-muted-foreground">{label}</span>
      <div className="relative flex-1 h-2 bg-gray-100 rounded-full overflow-visible">
        {/* Progress bar */}
        <div
          className={`absolute inset-y-0 left-0 rounded-full ${colorClass(pct)}`}
          style={{ width: `${displayPct}%` }}
        />
        {/* Goal marker for origin */}
        {showGoal && (
          <div
            className="absolute inset-y-[-4px] w-0.5 bg-blue-400"
            style={{ left: `${goalPct}%` }}
            title="Goal: 70%"
          />
        )}
      </div>
      <span className={`w-10 shrink-0 text-right text-xs font-semibold tabular-nums ${textColorClass(pct)}`}>
        {pct}%
      </span>
      {showGoal && (
        <span className="text-[10px] text-blue-400 shrink-0">Goal: 70%</span>
      )}
    </div>
  );
}

export function MetadataFillRateWidget({ fillRates }: MetadataFillRateWidgetProps) {
  if (!fillRates) {
    return (
      <div className="space-y-2">
        {["Origin", "Process", "Roast", "Variety"].map((label) => (
          <div key={label} className="flex items-center gap-3">
            <span className="w-16 shrink-0 text-xs text-muted-foreground">{label}</span>
            <div className="flex-1 h-2 bg-gray-100 rounded-full animate-pulse" />
            <span className="w-10 text-right text-xs text-muted-foreground">--</span>
          </div>
        ))}
      </div>
    );
  }

  const rows: FillRow[] = [
    { label: "Origin", pct: fillRates.origin_pct, showGoal: true },
    { label: "Process", pct: fillRates.process_pct },
    { label: "Roast", pct: fillRates.roast_pct },
    { label: "Variety", pct: fillRates.variety_pct },
  ];

  const count = fillRates.coffee_product_count ?? 0;

  return (
    <div className="space-y-2">
      {rows.map((row) => (
        <FillRateRow key={row.label} {...row} />
      ))}
      {count > 0 && (
        <p className="text-[10px] text-muted-foreground pt-1">
          Based on {count} coffee product{count === 1 ? "" : "s"}
        </p>
      )}
    </div>
  );
}
