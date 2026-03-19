import { createLazyFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useRecommendations,
  useRequestRecommendation,
  type RecommendationCandidateOut,
  type RecommendationResultResponse,
  type RecommendationRunSchema,
  type FilteredCandidateOut,
  type ScoreBreakdown,
} from "@/hooks/use-recommendations";

export const Route = createLazyFileRoute("/recommend")({
  component: RecommendPage,
});

// ─── helpers ────────────────────────────────────────────────────────────────

function fmtPrice(cents: number) {
  return `$${(cents / 100).toFixed(2)}`;
}

function fmtPricePerOz(cents: number | null) {
  if (!cents) return null;
  return `$${(cents / 100).toFixed(2)}/oz`;
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 80
      ? "bg-green-500"
      : pct >= 60
        ? "bg-amber-500"
        : "bg-red-400";
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-28 text-muted-foreground shrink-0">{label}</span>
      <div className="flex-1 bg-muted rounded-full h-1.5 overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-8 text-right font-medium">{pct}%</span>
    </div>
  );
}

function ScoreBreakdownPanel({ breakdown }: { breakdown: ScoreBreakdown }) {
  const rows: [string, number, number | undefined][] = [
    ["Merchant quality", breakdown.merchant_score, breakdown.weights.merchant],
    ["Quantity fit", breakdown.quantity_score, breakdown.weights.quantity],
    ["Espresso match", breakdown.espresso_score, breakdown.weights.espresso],
    ["Deal value", breakdown.deal_score, breakdown.weights.deal],
    ["Freshness", breakdown.freshness_score, breakdown.weights.freshness],
    ["Purchase history", breakdown.history_score, breakdown.weights.history],
    ["Promo bonus", breakdown.promo_bonus, undefined],
  ];

  return (
    <details className="mt-2 group">
      <summary className="cursor-pointer text-xs text-muted-foreground hover:text-foreground select-none list-none flex items-center gap-1">
        <span className="group-open:rotate-90 transition-transform inline-block">▶</span>
        Score breakdown
      </summary>
      <div className="mt-2 space-y-1.5 pl-3 border-l border-border/50">
        {rows.map(([label, value, weight]) => (
          <div key={label} className="flex items-center gap-2 text-xs">
            <span className="w-32 text-muted-foreground shrink-0">{label}</span>
            <div className="flex-1 bg-muted rounded-full h-1.5 overflow-hidden">
              <div
                className={`h-full rounded-full ${value >= 0.8 ? "bg-green-500" : value >= 0.6 ? "bg-amber-500" : value > 0 ? "bg-red-400" : "bg-muted-foreground/30"}`}
                style={{ width: `${Math.round(Math.min(value, 1) * 100)}%` }}
              />
            </div>
            <span className="w-8 text-right font-medium">{(value * 100).toFixed(0)}%</span>
            {weight !== undefined && (
              <span className="w-10 text-right text-muted-foreground/60">×{Math.round(weight * 100)}%</span>
            )}
          </div>
        ))}
        <div className="flex items-center justify-between text-xs font-medium pt-1 border-t border-border/50">
          <span>Total</span>
          <span>{(breakdown.total * 100).toFixed(1)}%</span>
        </div>
      </div>
    </details>
  );
}

function ResultCard({
  candidate,
  rank,
  explainScores,
}: {
  candidate: RecommendationCandidateOut;
  rank: number;
  explainScores?: boolean;
}) {
  const isTop = rank === 1;
  const discounted = candidate.discounted_landed_price_cents;
  const original = candidate.landed_price_cents;
  const perOz = fmtPricePerOz(candidate.landed_price_per_oz_cents);

  return (
    <Card
      className={`transition-shadow hover:shadow-md ${
        isTop
          ? "border-2 border-amber-700 shadow-md bg-amber-50/40"
          : "border border-border"
      }`}
    >
      {isTop && (
        <div className="px-4 pt-3 pb-0">
          <Badge className="bg-amber-700 text-white text-xs">⭐ Top Pick</Badge>
        </div>
      )}

      <CardHeader className="pb-2">
        <div className="flex gap-4">
          {/* Product image */}
          {candidate.image_url ? (
            <img
              src={candidate.image_url}
              alt={candidate.product_name}
              className="w-16 h-16 object-cover rounded-md border shrink-0"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = "none";
              }}
            />
          ) : (
            <div className="w-16 h-16 rounded-md border bg-amber-100 flex items-center justify-center shrink-0">
              <span className="text-2xl">☕</span>
            </div>
          )}

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div>
                <CardTitle className="text-base leading-tight">
                  {candidate.product_name}
                </CardTitle>
                <p className="text-sm text-muted-foreground mt-0.5">
                  {candidate.merchant_name}
                </p>
                {candidate.variant_label && (
                  <p className="text-xs text-muted-foreground">
                    {candidate.variant_label}
                  </p>
                )}
              </div>
              <div className="text-right shrink-0">
                {discounted ? (
                  <>
                    <p className="text-lg font-bold text-green-700">
                      {fmtPrice(discounted)}
                    </p>
                    <p className="text-xs text-muted-foreground line-through">
                      {fmtPrice(original)}
                    </p>
                  </>
                ) : (
                  <p className="text-lg font-bold">{fmtPrice(original)}</p>
                )}
                {perOz && (
                  <p className="text-xs text-muted-foreground">{perOz}</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Promo badge */}
        {candidate.best_promo_label && (
          <Badge variant="outline" className="text-green-700 border-green-300 bg-green-50 text-xs">
            🏷 {candidate.best_promo_label}
          </Badge>
        )}

        {/* Pros */}
        {candidate.pros.length > 0 && (
          <ul className="space-y-0.5">
            {candidate.pros.map((pro, i) => (
              <li key={i} className="text-xs text-muted-foreground flex gap-1.5">
                <span className="text-green-600 shrink-0">✓</span>
                {pro}
              </li>
            ))}
          </ul>
        )}

        {/* Score */}
        <div className="space-y-1.5 pt-1 border-t border-border/50">
          <ScoreBar label="Match Score" value={candidate.score} />
          {explainScores && candidate.score_breakdown && (
            <ScoreBreakdownPanel breakdown={candidate.score_breakdown} />
          )}
        </div>

        {/* Buy link */}
        <a
          href={candidate.product_url}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-amber-800 hover:text-amber-900 hover:underline"
        >
          Buy →
        </a>
      </CardContent>
    </Card>
  );
}

function WaitCard() {
  return (
    <Card className="border-2 border-dashed border-amber-300 bg-amber-50/60">
      <CardContent className="py-10 text-center space-y-3">
        <div className="text-4xl">⏳</div>
        <h3 className="font-semibold text-lg">Not Yet</h3>
        <p className="text-muted-foreground text-sm max-w-xs mx-auto">
          The recommendation engine couldn't find a strong enough match right now.
          Try again after the next crawl runs, or adjust your preferences.
        </p>
      </CardContent>
    </Card>
  );
}

function ResultsSkeleton() {
  return (
    <div className="space-y-3">
      {[0, 1, 2].map((i) => (
        <Card key={i}>
          <CardHeader className="pb-2">
            <div className="flex gap-4">
              <Skeleton className="w-16 h-16 rounded-md shrink-0" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-2/3" />
                <Skeleton className="h-3 w-1/2" />
              </div>
              <Skeleton className="h-6 w-16 shrink-0" />
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-4/5" />
            <Skeleton className="h-2 w-full rounded-full" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// ─── history helpers ─────────────────────────────────────────────────────────

function parseTopResult(run: RecommendationRunSchema) {
  try {
    return JSON.parse(run.top_result_json);
  } catch {
    return null;
  }
}

function parseRequest(run: RecommendationRunSchema) {
  try {
    return JSON.parse(run.request_json);
  } catch {
    return null;
  }
}

function HistoryItem({
  run,
  selected,
  onSelect,
}: {
  run: RecommendationRunSchema;
  selected: boolean;
  onSelect: () => void;
}) {
  const top = parseTopResult(run);
  const req = parseRequest(run);
  const date = new Date(run.run_at).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <button
      onClick={onSelect}
      className={`w-full text-left px-3 py-2.5 rounded-lg border transition-colors text-sm ${
        selected
          ? "border-amber-700 bg-amber-50"
          : "border-border hover:border-amber-400 hover:bg-amber-50/30"
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className="font-medium truncate">
            {top ? top.product_name : run.wait_recommendation ? "No match" : "—"}
          </p>
          <p className="text-xs text-muted-foreground">
            {req?.shot_style ?? "—"} · {req?.quantity_mode ?? "—"}
          </p>
        </div>
        <span className="text-xs text-muted-foreground shrink-0">{date}</span>
      </div>
    </button>
  );
}

// ─── Request form ─────────────────────────────────────────────────────────────

const SHOT_STYLES = [
  { value: "modern_58mm", label: "58mm Modern Espresso" },
  { value: "lever_49mm", label: "49mm Lever / Cremina" },
  { value: "turbo", label: "Turbo Shot" },
  { value: "experimental", label: "Experimental" },
];

const QUANTITY_MODES = [
  { value: "12-18 oz", label: "12–18 oz" },
  { value: "2lb", label: "2 lb" },
  { value: "5lb", label: "5 lb" },
  { value: "any", label: "Any Size" },
];

// ─── Main page ────────────────────────────────────────────────────────────────

function RecommendPage() {
  const navigate = useNavigate({ from: "/recommend" });
  const search = Route.useSearch();
  const [shotStyle, setShotStyle] = useState("modern_58mm");
  const [quantityMode, setQuantityMode] = useState("12-18 oz");
  const [bulkAllowed, setBulkAllowed] = useState(false);
  const [allowDecaf, setAllowDecaf] = useState(false);
  const [explainScores, setExplainScores] = useState(false);

  const [activeResult, setActiveResult] =
    useState<RecommendationResultResponse | null>(null);
  const [selectedHistoryId, setSelectedHistoryId] = useState<number | null>(null);

  const { data: history = [], isLoading: historyLoading } = useRecommendations();
  const request = useRequestRecommendation();

  useEffect(() => {
    if (!search.selectedRunId || history.length === 0) return;
    if (selectedHistoryId === search.selectedRunId) return;

    const linkedRun = history.find((run) => run.id === search.selectedRunId);
    if (linkedRun) {
      handleSelectHistory(linkedRun);
    }
  }, [history, search.selectedRunId, selectedHistoryId]);

  function handleGetRecs() {
    setSelectedHistoryId(null);
    request.mutate(
      {
        shot_style: shotStyle,
        quantity_mode: quantityMode,
        bulk_allowed: bulkAllowed,
        allow_decaf: allowDecaf,
        current_inventory_grams: 0,
        explain_scores: explainScores,
      },
      {
        onSuccess: (data) => {
          setActiveResult(data);
        },
      }
    );
  }

  function handleSelectHistory(run: RecommendationRunSchema) {
    setSelectedHistoryId(run.id);
    try {
      const top = JSON.parse(run.top_result_json);
      const alternatives = JSON.parse(run.alternatives_json);
      setActiveResult({
        top_result: top,
        alternatives: Array.isArray(alternatives) ? alternatives : [],
        wait_recommendation: run.wait_recommendation,
        run_id: run.id,
      });
    } catch {
      setActiveResult(null);
    }
  }

  const showResults = activeResult !== null || request.isPending;

  return (
    <div className="max-w-5xl mx-auto space-y-6 p-4 md:p-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">☕ Recommendations</h1>
        <p className="text-muted-foreground mt-1">
          Dial in your shot style and get the best bag for your setup
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-[320px_1fr] gap-6">
        {/* ── Left panel: form ── */}
        <div className="space-y-4">
          <Card className="shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Configure</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Shot Style */}
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Shot Style</label>
                <Select value={shotStyle} onValueChange={setShotStyle}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {SHOT_STYLES.map((s) => (
                      <SelectItem key={s.value} value={s.value}>
                        {s.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Bag Size */}
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Bag Size</label>
                <Select value={quantityMode} onValueChange={setQuantityMode}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {QUANTITY_MODES.map((q) => (
                      <SelectItem key={q.value} value={q.value}>
                        {q.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Toggles */}
              <div className="space-y-2 pt-1">
                <label className="flex items-center gap-2.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={bulkAllowed}
                    onChange={(e) => setBulkAllowed(e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm">Include bulk bags</span>
                </label>
                <label className="flex items-center gap-2.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={allowDecaf}
                    onChange={(e) => setAllowDecaf(e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm">Allow decaf options</span>
                </label>
                <label className="flex items-center gap-2.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={explainScores}
                    onChange={(e) => setExplainScores(e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm">Explain scores</span>
                </label>
              </div>

              <Button
                onClick={handleGetRecs}
                disabled={request.isPending}
                className="w-full bg-amber-800 hover:bg-amber-900 text-white"
              >
                {request.isPending ? (
                  <span className="flex items-center gap-2">
                    <span className="animate-spin">⟳</span> Finding best bag…
                  </span>
                ) : (
                  "🎯 Get Recommendations"
                )}
              </Button>
            </CardContent>
          </Card>

          {/* History */}
          <Card className="shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">History</CardTitle>
            </CardHeader>
            <CardContent className="space-y-1.5 max-h-72 overflow-y-auto">
              {historyLoading ? (
                <div className="space-y-2">
                  {[0, 1, 2].map((i) => (
                    <Skeleton key={i} className="h-12 w-full rounded-lg" />
                  ))}
                </div>
              ) : history.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No runs yet. Click Get Recommendations!
                </p>
              ) : (
                history.map((run) => (
                  <HistoryItem
                    key={run.id}
                    run={run}
                    selected={selectedHistoryId === run.id}
                    onSelect={() => handleSelectHistory(run)}
                  />
                ))
              )}
            </CardContent>
          </Card>
        </div>

        {/* ── Right panel: results ── */}
        <div>
          {request.isPending ? (
            <ResultsSkeleton />
          ) : !showResults ? (
            <div className="flex flex-col items-center justify-center h-64 text-center text-muted-foreground border-2 border-dashed border-border rounded-xl">
              <span className="text-4xl mb-3">☕</span>
              <p className="font-medium">Configure your preferences</p>
              <p className="text-sm mt-1">
                Set your shot style and hit Get Recommendations
              </p>
            </div>
          ) : activeResult?.wait_recommendation ? (
            <WaitCard />
          ) : activeResult ? (
            <div className="space-y-4">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-muted-foreground">
                  {activeResult.alternatives.length + (activeResult.top_result ? 1 : 0)} results
                  {selectedHistoryId ? " (from history)" : ""}
                </p>
                {activeResult.run_id ? (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      void navigate({
                        to: "/purchases",
                        search: { recommendationRunId: activeResult.run_id },
                      });
                    }}
                  >
                    🛒 Log purchase from this run
                  </Button>
                ) : null}
              </div>

              {activeResult.top_result && (
                <ResultCard candidate={activeResult.top_result} rank={1} explainScores={explainScores} />
              )}

              {activeResult.alternatives.length > 0 && (
                <>
                  <h3 className="text-sm font-medium text-muted-foreground">
                    Alternatives
                  </h3>
                  <div className="space-y-3">
                    {activeResult.alternatives.map((alt, i) => (
                      <ResultCard key={i} candidate={alt} rank={i + 2} explainScores={explainScores} />
                    ))}
                  </div>
                </>
              )}

              {/* Filtered candidates panel (explain mode only) */}
              {explainScores && activeResult.filtered_candidates && activeResult.filtered_candidates.length > 0 && (
                <details className="mt-4">
                  <summary className="cursor-pointer text-xs font-medium text-muted-foreground hover:text-foreground select-none list-none flex items-center gap-1">
                    <span>▶</span>
                    {activeResult.filtered_candidates.length} filtered out
                  </summary>
                  <div className="mt-2 border rounded-lg overflow-hidden">
                    <table className="w-full text-xs">
                      <thead className="bg-muted">
                        <tr>
                          <th className="text-left px-3 py-1.5 font-medium">Product</th>
                          <th className="text-left px-3 py-1.5 font-medium">Reason</th>
                        </tr>
                      </thead>
                      <tbody>
                        {activeResult.filtered_candidates.map((fc: FilteredCandidateOut, i: number) => (
                          <tr key={i} className="border-t border-border/50">
                            <td className="px-3 py-1.5 text-muted-foreground">
                              {fc.merchant_name} — {fc.product_name}
                              {fc.variant_label && <span className="text-muted-foreground/60"> ({fc.variant_label})</span>}
                            </td>
                            <td className="px-3 py-1.5 text-red-600">{fc.filter_reason}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </details>
              )}
            </div>
          ) : null}

          {/* Error state */}
          {request.isError && (
            <Card className="border-red-200 bg-red-50">
              <CardContent className="py-6 text-center">
                <p className="text-red-700 font-medium">Something went wrong</p>
                <p className="text-sm text-red-600 mt-1">
                  {(request.error as Error)?.message ?? "Failed to get recommendations"}
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-3"
                  onClick={handleGetRecs}
                >
                  Try Again
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
