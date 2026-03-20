import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useBuyingPatterns } from "@/hooks/use-purchases";

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-base font-semibold">{value}</p>
    </div>
  );
}

/**
 * PurchaseStatsCard — shows behavioural buying intelligence from purchase history.
 * Displays: days since last order, top 3 roasters, avg grams/week.
 */
export function PurchaseStatsCard() {
  const { data, isLoading, isError } = useBuyingPatterns();

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">My buying patterns</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-10 rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isError || !data) return null;

  const { days_since_last_order, top_roasters, avg_grams_per_week } = data;

  const daysSince =
    days_since_last_order === null || days_since_last_order === undefined
      ? "–"
      : days_since_last_order === 0
        ? "Today"
        : days_since_last_order === 1
          ? "Yesterday"
          : `${days_since_last_order}d ago`;

  const avgGrams =
    avg_grams_per_week === null || avg_grams_per_week === undefined
      ? "–"
      : `${avg_grams_per_week.toFixed(0)}g/wk`;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          ☕ My buying patterns
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Stat label="Last order" value={daysSince} />
          <Stat label="Avg per week" value={avgGrams} />
          <div className="flex flex-col gap-0.5 sm:col-span-1">
            <p className="text-xs text-muted-foreground">Top roasters</p>
            {top_roasters.length === 0 ? (
              <p className="text-base font-semibold">–</p>
            ) : (
              <ul className="text-sm space-y-0.5">
                {top_roasters.slice(0, 3).map((r) => (
                  <li key={r.merchant_name} className="flex items-center gap-1.5">
                    <span className="font-medium truncate">{r.merchant_name}</span>
                    <span className="text-muted-foreground text-xs shrink-0">
                      ×{r.count}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

