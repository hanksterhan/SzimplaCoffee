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
import { useMerchants } from "@/hooks/use-merchants";
import { useAddPurchase, useUpdatePurchase } from "@/hooks/use-purchases";
import type { PurchaseSummary } from "@/hooks/use-purchases";

const WEIGHT_PRESETS = [
  { label: "12 oz (340g)", grams: 340 },
  { label: "1 lb (454g)", grams: 454 },
  { label: "2 lb (907g)", grams: 907 },
  { label: "5 lb (2268g)", grams: 2268 },
  { label: "Custom", grams: 0 },
] as const;

interface FormState {
  merchant_id: string;
  product_name: string;
  origin_text: string;
  process_text: string;
  price_dollars: string;
  weight_preset: string;
  weight_custom: string;
  purchased_at: string;
}

function toISODate(d: Date) {
  return d.toISOString().slice(0, 10);
}

function purchaseToForm(p: PurchaseSummary): FormState {
  const preset = WEIGHT_PRESETS.find((w) => w.grams === p.weight_grams && w.grams !== 0);
  return {
    merchant_id: String(p.merchant_id),
    product_name: p.product_name,
    origin_text: p.origin_text,
    process_text: p.process_text,
    price_dollars: (p.price_cents / 100).toFixed(2),
    weight_preset: preset ? String(preset.grams) : "0",
    weight_custom: preset ? "" : String(p.weight_grams),
    purchased_at: toISODate(new Date(p.purchased_at)),
  };
}

const DEFAULT_FORM: FormState = {
  merchant_id: "",
  product_name: "",
  origin_text: "",
  process_text: "",
  price_dollars: "",
  weight_preset: "340",
  weight_custom: "",
  purchased_at: toISODate(new Date()),
};

interface PurchaseFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editPurchase?: PurchaseSummary;
}

export function PurchaseForm({ open, onOpenChange, editPurchase }: PurchaseFormProps) {
  const [form, setForm] = useState<FormState>(
    editPurchase ? purchaseToForm(editPurchase) : DEFAULT_FORM
  );
  const [merchantSelectOpen, setMerchantSelectOpen] = useState(false);
  const [weightSelectOpen, setWeightSelectOpen] = useState(false);

  const { data: merchantsData } = useMerchants({ page_size: 200, is_active: true });
  const merchants = merchantsData?.items ?? [];

  const { mutate: addPurchase, isPending: isAdding } = useAddPurchase();
  const { mutate: updatePurchase, isPending: isUpdating } = useUpdatePurchase();
  const isPending = isAdding || isUpdating;

  function getWeightGrams(): number {
    if (form.weight_preset === "0") {
      return parseInt(form.weight_custom) || 0;
    }
    return parseInt(form.weight_preset);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const body = {
      merchant_id: parseInt(form.merchant_id),
      product_name: form.product_name,
      origin_text: form.origin_text,
      process_text: form.process_text,
      price_cents: Math.round(parseFloat(form.price_dollars) * 100),
      weight_grams: getWeightGrams(),
      purchased_at: new Date(form.purchased_at).toISOString(),
      source_system: "manual",
      source_ref: "",
    };
    if (editPurchase) {
      updatePurchase(
        { id: editPurchase.id, body },
        {
          onSuccess: () => {
            onOpenChange(false);
          },
        }
      );
    } else {
      addPurchase(body, {
        onSuccess: () => {
          setForm(DEFAULT_FORM);
          onOpenChange(false);
        },
      });
    }
  }

  function set(field: keyof FormState, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{editPurchase ? "Edit Purchase" : "Log Purchase"}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 py-2">
          {/* Merchant */}
          <div className="space-y-1">
            <label className="text-sm font-medium">Merchant *</label>
            <Select value={form.merchant_id} onValueChange={(v) => set("merchant_id", v)} open={merchantSelectOpen} onOpenChange={setMerchantSelectOpen}>
              <SelectTrigger onOpenToggle={() => setMerchantSelectOpen(true)}>
                <SelectValue placeholder="Select merchant…" />
              </SelectTrigger>
              <SelectContent>
                {merchants.map((m) => (
                  <SelectItem key={m.id} value={String(m.id)}>
                    {m.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Product name */}
          <div className="space-y-1">
            <label className="text-sm font-medium">Product Name *</label>
            <Input
              required
              value={form.product_name}
              onChange={(e) => set("product_name", e.target.value)}
              placeholder="e.g. Ethiopia Yirgacheffe Natural"
            />
          </div>

          {/* Origin + Process */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-sm font-medium">Origin</label>
              <Input
                value={form.origin_text}
                onChange={(e) => set("origin_text", e.target.value)}
                placeholder="Ethiopia"
              />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium">Process</label>
              <Input
                value={form.process_text}
                onChange={(e) => set("process_text", e.target.value)}
                placeholder="Natural"
              />
            </div>
          </div>

          {/* Price + Weight */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-sm font-medium">Price ($) *</label>
              <Input
                required
                type="number"
                step="0.01"
                min="0"
                value={form.price_dollars}
                onChange={(e) => set("price_dollars", e.target.value)}
                placeholder="18.00"
              />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium">Weight</label>
              <Select
                value={form.weight_preset}
                onValueChange={(v) => set("weight_preset", v)}
                open={weightSelectOpen}
                onOpenChange={setWeightSelectOpen}
              >
                <SelectTrigger onOpenToggle={() => setWeightSelectOpen(true)}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {WEIGHT_PRESETS.map((w) => (
                    <SelectItem key={w.grams} value={String(w.grams)}>
                      {w.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Custom weight */}
          {form.weight_preset === "0" && (
            <div className="space-y-1">
              <label className="text-sm font-medium">Custom Weight (grams)</label>
              <Input
                type="number"
                min="1"
                value={form.weight_custom}
                onChange={(e) => set("weight_custom", e.target.value)}
                placeholder="250"
              />
            </div>
          )}

          {/* Date */}
          <div className="space-y-1">
            <label className="text-sm font-medium">Date Purchased</label>
            <Input
              type="date"
              value={form.purchased_at}
              onChange={(e) => set("purchased_at", e.target.value)}
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isPending || !form.merchant_id || !form.product_name || !form.price_dollars}
            >
              {isPending ? "Saving…" : editPurchase ? "Update" : "Log Purchase"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
