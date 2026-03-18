import { useNavigate } from "@tanstack/react-router";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { PurchaseSummary } from "@/hooks/use-purchases";

interface PurchaseDetailDrawerProps {
  purchase: PurchaseSummary | null;
  merchantName: string;
  onClose: () => void;
  onEdit: (p: PurchaseSummary) => void;
  onDelete: (p: PurchaseSummary) => void;
}

function fmtPrice(cents: number) {
  return `$${(cents / 100).toFixed(2)}`;
}

function fmtWeight(grams: number) {
  if (grams >= 454) return `${(grams / 453.6).toFixed(1)} lb`;
  return `${grams}g`;
}

function fmtPricePerLb(cents: number, grams: number) {
  if (!grams) return "–";
  const perLb = cents / (grams / 453.6);
  return `$${(perLb / 100).toFixed(2)}/lb`;
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    weekday: "short",
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

export function PurchaseDetailDrawer({
  purchase,
  merchantName,
  onClose,
  onEdit,
  onDelete,
}: PurchaseDetailDrawerProps) {
  const navigate = useNavigate();

  if (!purchase) return null;

  function openRecommendationRun(runId: number) {
    void navigate({ to: "/recommend", search: { selectedRunId: runId } });
    onClose();
  }

  const hasRecommendation = purchase.recommendation_run_id != null;

  return (
    <Dialog open={!!purchase} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="text-base font-semibold truncate pr-8">
            {purchase.product_name}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-1">
          {/* Core facts */}
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-muted-foreground text-xs mb-0.5">Date</p>
              <p className="font-medium">{fmtDate(purchase.purchased_at)}</p>
            </div>
            <div>
              <p className="text-muted-foreground text-xs mb-0.5">Merchant</p>
              <p className="font-medium">{merchantName}</p>
            </div>
            <div>
              <p className="text-muted-foreground text-xs mb-0.5">Price</p>
              <p className="font-medium">{fmtPrice(purchase.price_cents)}</p>
            </div>
            <div>
              <p className="text-muted-foreground text-xs mb-0.5">Weight</p>
              <p className="font-medium">{fmtWeight(purchase.weight_grams)}</p>
            </div>
            <div>
              <p className="text-muted-foreground text-xs mb-0.5">Price/lb</p>
              <p className="font-medium">
                {fmtPricePerLb(purchase.price_cents, purchase.weight_grams)}
              </p>
            </div>
            {(purchase.origin_text || purchase.process_text) && (
              <div>
                <p className="text-muted-foreground text-xs mb-0.5">Coffee</p>
                <p className="font-medium">
                  {[purchase.origin_text, purchase.process_text]
                    .filter(Boolean)
                    .join(" · ")}
                </p>
              </div>
            )}
          </div>

          {/* Recommendation context */}
          {hasRecommendation ? (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm">🎯</span>
                  <span className="text-sm font-medium text-emerald-900">
                    Linked to recommendation run #{purchase.recommendation_run_id}
                  </span>
                </div>
                <Badge
                  variant="outline"
                  className="text-xs border-emerald-300 text-emerald-800"
                >
                  rec-linked
                </Badge>
              </div>
              <p className="text-xs text-emerald-800/80">
                This purchase was made from a recommendation. You can revisit
                the original run to see what was ranked and why.
              </p>
              <Button
                size="sm"
                variant="outline"
                className="w-full border-emerald-300 text-emerald-800 hover:bg-emerald-100"
                onClick={() =>
                  openRecommendationRun(purchase.recommendation_run_id!)
                }
              >
                Open recommendation run →
              </Button>
            </div>
          ) : (
            <div className="rounded-lg border border-dashed p-3 text-xs text-muted-foreground flex items-center gap-2">
              <span>📝</span>
              <span>Manually logged — not linked to a recommendation run.</span>
            </div>
          )}

          {/* Feedback summary */}
          {purchase.feedback_count > 0 && (
            <div className="text-sm">
              <p className="text-muted-foreground text-xs mb-1">Brew Sessions</p>
              <Badge variant="secondary">
                {purchase.feedback_count} session
                {purchase.feedback_count !== 1 ? "s" : ""} logged
              </Badge>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2 pt-2 border-t">
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            onClick={() => {
              onEdit(purchase);
              onClose();
            }}
          >
            ✏️ Edit
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="flex-1 text-destructive hover:text-destructive"
            onClick={() => {
              onDelete(purchase);
              onClose();
            }}
          >
            🗑️ Delete
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
