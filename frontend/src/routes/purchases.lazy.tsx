import { createLazyFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { PurchaseForm } from "@/components/purchases/PurchaseForm";
import { BrewFeedbackForm } from "@/components/purchases/BrewFeedbackForm";
import { usePurchases, usePurchaseStats, useDeletePurchase } from "@/hooks/use-purchases";
import { usePurchaseFeedback } from "@/hooks/use-feedback";
import { useMerchants } from "@/hooks/use-merchants";
import type { PurchaseSummary } from "@/hooks/use-purchases";

export const Route = createLazyFileRoute("/purchases")({
  component: PurchasesPage,
});

// ── Helpers ──────────────────────────────────────────────────────────────────

function fmtPrice(cents: number) {
  return `$${(cents / 100).toFixed(2)}`;
}

function fmtWeight(grams: number) {
  if (grams >= 907) return `${(grams / 453.6).toFixed(1)} lb`;
  if (grams >= 454) return `${(grams / 453.6).toFixed(1)} lb`;
  return `${grams}g`;
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function fmtPricePerLb(cents: number, grams: number) {
  if (!grams) return "–";
  const perLb = cents / (grams / 453.6);
  return `$${(perLb / 100).toFixed(2)}/lb`;
}

// ── Stats ────────────────────────────────────────────────────────────────────

function StatsBar() {
  const { data: stats, isLoading } = usePurchaseStats();

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-20 rounded-lg" />
        ))}
      </div>
    );
  }

  if (!stats) return null;

  const cards = [
    { label: "Total Purchases", value: String(stats.total_purchases) },
    { label: "Total Spent", value: fmtPrice(stats.total_spent_cents) },
    {
      label: "Avg $/lb",
      value: fmtPrice(Math.round(stats.avg_price_per_lb_cents)),
    },
    {
      label: "Favorite Merchant",
      value: stats.favorite_merchant_name ?? "–",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      {cards.map((c) => (
        <div
          key={c.label}
          className="rounded-lg border bg-card p-4 flex flex-col gap-1"
        >
          <p className="text-xs text-muted-foreground">{c.label}</p>
          <p className="text-xl font-bold truncate">{c.value}</p>
        </div>
      ))}
    </div>
  );
}

// ── Inline Feedback Rows ──────────────────────────────────────────────────────

function FeedbackRows({ purchase }: { purchase: PurchaseSummary }) {
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const hasFeedback = purchase.feedback_count > 0;

  return (
    <>
      <TableRow className="bg-muted/30">
        <TableCell colSpan={7} className="py-2 px-6">
          <div className="flex items-center gap-3">
            {hasFeedback && (
              <button
                type="button"
                onClick={() => setExpanded((v) => !v)}
                className="text-xs text-blue-600 hover:underline"
              >
                {expanded ? "▲ Hide" : "▼ Show"} {purchase.feedback_count} brew
                session{purchase.feedback_count !== 1 ? "s" : ""}
              </button>
            )}
            <button
              type="button"
              onClick={() => setFeedbackOpen(true)}
              className="text-xs text-amber-700 hover:underline"
            >
              + Add Feedback
            </button>
          </div>

          {expanded && hasFeedback && (
            <FeedbackDetail purchaseId={purchase.id} />
          )}
        </TableCell>
      </TableRow>

      <BrewFeedbackForm
        purchaseId={purchase.id}
        purchaseName={purchase.product_name}
        open={feedbackOpen}
        onOpenChange={setFeedbackOpen}
      />
    </>
  );
}

function FeedbackDetail({ purchaseId }: { purchaseId: number }) {
  const { data: feedbacks, isLoading } = usePurchaseFeedback(purchaseId);

  if (isLoading) return <p className="text-xs text-muted-foreground mt-2">Loading…</p>;
  if (!feedbacks?.length) return null;

  return (
    <div className="mt-2 space-y-2">
      {feedbacks.map((fb) => (
        <div
          key={fb.id}
          className="rounded border bg-background p-3 text-xs grid grid-cols-2 md:grid-cols-4 gap-2"
        >
          <div>
            <span className="text-muted-foreground">Style: </span>
            {fb.shot_style}
          </div>
          <div>
            <span className="text-muted-foreground">Grinder: </span>
            {fb.grinder || "–"}
          </div>
          <div>
            <span className="text-muted-foreground">Basket: </span>
            {fb.basket || "–"}
          </div>
          <div>
            <span className="text-muted-foreground">Rating: </span>
            {"⭐".repeat(Math.round(fb.rating))} ({fb.rating}/5)
          </div>
          <div>
            <span className="text-muted-foreground">Difficulty: </span>
            {fb.difficulty_score}/5
          </div>
          <div>
            <span className="text-muted-foreground">Rebuy: </span>
            {fb.would_rebuy ? "✅ Yes" : "❌ No"}
          </div>
          {fb.notes && (
            <div className="col-span-2 md:col-span-4">
              <span className="text-muted-foreground">Notes: </span>
              {fb.notes}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

function PurchasesPage() {
  const [logOpen, setLogOpen] = useState(false);
  const [editPurchase, setEditPurchase] = useState<PurchaseSummary | null>(null);
  const [filterMerchantId, setFilterMerchantId] = useState<string>("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const { data: merchantsData } = useMerchants({ page_size: 200, is_active: true });
  const merchants = merchantsData?.items ?? [];

  const { data: purchases, isLoading } = usePurchases({
    merchant_id: filterMerchantId ? parseInt(filterMerchantId) : undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
  });

  const { mutate: deletePurchase } = useDeletePurchase();

  function handleDelete(p: PurchaseSummary) {
    if (confirm(`Delete purchase of "${p.product_name}"?`)) {
      deletePurchase(p.id);
    }
  }

  function merchantName(id: number) {
    return merchants.find((m) => m.id === id)?.name ?? `#${id}`;
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Purchases</h1>
          <p className="text-sm text-muted-foreground">
            Track your coffee purchases and brew feedback
          </p>
        </div>
        <Button onClick={() => setLogOpen(true)}>🛒 Log Purchase</Button>
      </div>

      {/* Stats */}
      <StatsBar />

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <Select
          debugName="purchases.filter-merchant"
          value={filterMerchantId}
          onValueChange={setFilterMerchantId}
        >
          <SelectTrigger className="w-full sm:w-48">
            <SelectValue placeholder="All merchants" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">All merchants</SelectItem>
            {merchants.map((m) => (
              <SelectItem key={m.id} value={String(m.id)}>
                {m.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Input
          type="date"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          className="w-full sm:w-40"
          placeholder="From"
        />
        <Input
          type="date"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          className="w-full sm:w-40"
          placeholder="To"
        />
        {(filterMerchantId || dateFrom || dateTo) && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setFilterMerchantId("");
              setDateFrom("");
              setDateTo("");
            }}
          >
            Clear filters
          </Button>
        )}
      </div>

      {/* Table — scrollable on mobile */}
      {isLoading ? (
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : !purchases?.length ? (
        <div className="rounded-lg border border-dashed p-12 text-center text-muted-foreground">
          <p className="text-4xl mb-3">🛒</p>
          <p className="font-medium">No purchases yet</p>
          <p className="text-sm">Log your first coffee purchase to get started</p>
          <Button className="mt-4" onClick={() => setLogOpen(true)}>
            Log Purchase
          </Button>
        </div>
      ) : (
        <div className="rounded-md border overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Merchant</TableHead>
                <TableHead>Product</TableHead>
                <TableHead>Price</TableHead>
                <TableHead>Weight</TableHead>
                <TableHead>$/lb</TableHead>
                <TableHead>Feedback</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {purchases.map((p) => (
                <>
                  <TableRow key={p.id}>
                    <TableCell className="text-sm whitespace-nowrap">
                      {fmtDate(p.purchased_at)}
                    </TableCell>
                    <TableCell className="text-sm font-medium whitespace-nowrap">
                      {merchantName(p.merchant_id)}
                    </TableCell>
                    <TableCell>
                      <div className="font-medium text-sm">{p.product_name}</div>
                      {(p.origin_text || p.process_text) && (
                        <div className="text-xs text-muted-foreground">
                          {[p.origin_text, p.process_text].filter(Boolean).join(" · ")}
                        </div>
                      )}
                    </TableCell>
                    <TableCell className="text-sm whitespace-nowrap">{fmtPrice(p.price_cents)}</TableCell>
                    <TableCell className="text-sm whitespace-nowrap">{fmtWeight(p.weight_grams)}</TableCell>
                    <TableCell className="text-sm text-muted-foreground whitespace-nowrap">
                      {fmtPricePerLb(p.price_cents, p.weight_grams)}
                    </TableCell>
                    <TableCell>
                      {p.feedback_count > 0 ? (
                        <Badge variant="secondary">
                          {p.feedback_count} session{p.feedback_count !== 1 ? "s" : ""}
                        </Badge>
                      ) : (
                        <span className="text-xs text-muted-foreground">None</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setEditPurchase(p)}
                        >
                          ✏️
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleDelete(p)}
                        >
                          🗑️
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                  <FeedbackRows key={`fb-${p.id}`} purchase={p} />
                </>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {/* Dialogs */}
      <PurchaseForm open={logOpen} onOpenChange={setLogOpen} />
      {editPurchase && (
        <PurchaseForm
          open={!!editPurchase}
          onOpenChange={(open) => !open && setEditPurchase(null)}
          editPurchase={editPurchase}
        />
      )}
    </div>
  );
}
