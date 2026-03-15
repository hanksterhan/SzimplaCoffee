import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAddFeedback } from "@/hooks/use-feedback";
import type { BrewFeedbackCreate } from "@/hooks/use-feedback";

interface BrewFeedbackFormProps {
  purchaseId: number;
  purchaseName: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const SHOT_STYLES = [
  "58mm Modern",
  "49mm Lever",
  "Turbo",
  "Experimental",
] as const;

const BASKETS = ["58mm", "49mm step-down"] as const;

const DEFAULT_FORM: BrewFeedbackCreate = {
  shot_style: "58mm Modern",
  grinder: "Timemore Sculptor 078S",
  basket: "58mm",
  rating: 3,
  would_rebuy: true,
  difficulty_score: 3,
  notes: "",
};

export function BrewFeedbackForm({
  purchaseId,
  purchaseName,
  open,
  onOpenChange,
}: BrewFeedbackFormProps) {
  const [form, setForm] = useState<BrewFeedbackCreate>(DEFAULT_FORM);
  const { mutate: addFeedback, isPending } = useAddFeedback();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    addFeedback(
      { purchaseId, body: form },
      {
        onSuccess: () => {
          setForm(DEFAULT_FORM);
          onOpenChange(false);
        },
      }
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Add Brew Feedback</DialogTitle>
          <p className="text-sm text-muted-foreground truncate">{purchaseName}</p>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 py-2">
          {/* Shot style */}
          <div className="space-y-1">
            <label className="text-sm font-medium">Shot Style</label>
            <Select
              value={form.shot_style}
              onValueChange={(v) => setForm((f) => ({ ...f, shot_style: v }))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SHOT_STYLES.map((s) => (
                  <SelectItem key={s} value={s}>
                    {s}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Grinder */}
          <div className="space-y-1">
            <label className="text-sm font-medium">Grinder</label>
            <Input
              value={form.grinder}
              onChange={(e) => setForm((f) => ({ ...f, grinder: e.target.value }))}
              placeholder="Timemore Sculptor 078S"
            />
          </div>

          {/* Basket */}
          <div className="space-y-1">
            <label className="text-sm font-medium">Basket</label>
            <Select
              value={form.basket}
              onValueChange={(v) => setForm((f) => ({ ...f, basket: v }))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {BASKETS.map((b) => (
                  <SelectItem key={b} value={b}>
                    {b}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Rating */}
          <div className="space-y-1">
            <label className="text-sm font-medium">Rating (1–5)</label>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map((n) => (
                <button
                  key={n}
                  type="button"
                  onClick={() => setForm((f) => ({ ...f, rating: n }))}
                  className={`text-2xl transition-opacity ${
                    n <= form.rating ? "opacity-100" : "opacity-30"
                  }`}
                >
                  ⭐
                </button>
              ))}
            </div>
          </div>

          {/* Would rebuy */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="would-rebuy"
              checked={form.would_rebuy}
              onChange={(e) =>
                setForm((f) => ({ ...f, would_rebuy: e.target.checked }))
              }
              className="h-4 w-4"
            />
            <label htmlFor="would-rebuy" className="text-sm font-medium">
              Would rebuy
            </label>
          </div>

          {/* Difficulty */}
          <div className="space-y-1">
            <label className="text-sm font-medium">
              Dial-in Difficulty: {form.difficulty_score}/5
            </label>
            <input
              type="range"
              min={1}
              max={5}
              step={1}
              value={form.difficulty_score}
              onChange={(e) =>
                setForm((f) => ({ ...f, difficulty_score: Number(e.target.value) }))
              }
              className="w-full accent-amber-700"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Easy</span>
              <span>Hard</span>
            </div>
          </div>

          {/* Notes */}
          <div className="space-y-1">
            <label className="text-sm font-medium">Notes</label>
            <textarea
              value={form.notes}
              onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
              rows={3}
              placeholder="Tasting notes, dial-in observations…"
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none"
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? "Saving…" : "Save Feedback"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
