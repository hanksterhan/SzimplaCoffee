import { createFileRoute, useNavigate, Link } from "@tanstack/react-router";
import { useState } from "react";
import { useAddMerchant } from "@/hooks/use-merchants";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export const Route = createFileRoute("/merchants/new")({
  component: AddMerchantPage,
});

function detectPlatformFromUrl(url: string): string {
  if (url.includes("myshopify.com")) return "shopify";
  if (url.includes("woocommerce") || url.includes("wp-json/wc")) return "woocommerce";
  return "unknown";
}

function extractDomain(url: string): string {
  try {
    const u = new URL(url.startsWith("http") ? url : `https://${url}`);
    return u.hostname.replace(/^www\./, "");
  } catch {
    return url.replace(/^https?:\/\//, "").replace(/^www\./, "").split("/")[0];
  }
}

function AddMerchantPage() {
  const navigate = useNavigate();
  const [url, setUrl] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const { mutateAsync, isPending, error } = useAddMerchant();

  const domain = url.trim() ? extractDomain(url.trim()) : "";
  const detectedPlatform = url.trim() ? detectPlatformFromUrl(url.trim()) : "";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setSubmitted(true);
    try {
      const merchant = await mutateAsync({ url: url.trim() });
      if (merchant) {
        navigate({
          to: "/merchants/$merchantId",
          params: { merchantId: String(merchant.id) },
        });
      }
    } catch {
      // error is captured in mutation state
    }
  };

  return (
    <div className="max-w-lg space-y-6">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link to="/merchants" className="hover:underline">
          Merchants
        </Link>
        <span>/</span>
        <span className="text-foreground font-medium">Add Merchant</span>
      </div>

      <div>
        <h1 className="text-2xl font-bold">🏪 Add Merchant</h1>
        <p className="text-muted-foreground text-sm">
          Add a new coffee merchant to track
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Store URL</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1">
              <Input
                type="url"
                placeholder="https://store.myshopify.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={isPending}
                autoFocus
              />
              <p className="text-xs text-muted-foreground">
                Enter the store homepage URL (e.g. https://onibuscoffee.com)
              </p>
            </div>

            {/* Preview */}
            {domain && (
              <div className="rounded-lg border bg-muted/30 p-3 space-y-2">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Preview
                </p>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{domain}</span>
                  {detectedPlatform !== "unknown" && (
                    <Badge
                      variant="outline"
                      className="text-xs bg-blue-50 text-blue-700 border-blue-200"
                    >
                      {detectedPlatform}
                    </Badge>
                  )}
                  {detectedPlatform === "unknown" && (
                    <Badge variant="outline" className="text-xs text-muted-foreground">
                      platform unknown
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">
                  The platform will be confirmed after the first crawl.
                </p>
              </div>
            )}

            {/* Error */}
            {submitted && error && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-3">
                <p className="text-sm text-red-700">
                  {error instanceof Error ? error.message : "Failed to add merchant. Please try again."}
                </p>
              </div>
            )}

            <div className="flex gap-3">
              <Button
                type="submit"
                disabled={isPending || !url.trim()}
                className="flex-1"
              >
                {isPending ? "Adding…" : "Add Merchant"}
              </Button>
              <Link to="/merchants">
                <Button type="button" variant="outline">
                  Cancel
                </Button>
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>

      <div className="text-sm text-muted-foreground space-y-1">
        <p className="font-medium">What happens next:</p>
        <ul className="list-disc list-inside space-y-1 text-xs">
          <li>Merchant is created with "candidate" trust tier</li>
          <li>A crawl will be triggered to discover products</li>
          <li>Platform type will be auto-detected on first crawl</li>
        </ul>
      </div>
    </div>
  );
}
