# SC-24 Execution Plan: Add Merchant Page

## `frontend/src/lib/platform-detect.ts`
```typescript
export type PlatformType = "shopify" | "woocommerce" | "agentic" | "unknown";

export interface MerchantPreview {
  canonicalDomain: string;
  homepageUrl: string;
  suggestedName: string;
  platformType: PlatformType;
}

export function detectPlatform(url: string): MerchantPreview {
  let parsed: URL;
  try {
    parsed = new URL(url.startsWith("http") ? url : `https://${url}`);
  } catch {
    return { canonicalDomain: "", homepageUrl: url, suggestedName: "", platformType: "unknown" };
  }

  const hostname = parsed.hostname.replace(/^www\./, "");
  const platform = detectPlatformFromHostname(hostname, url);
  const name = hostname.split(".")[0].replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  return {
    canonicalDomain: hostname,
    homepageUrl: `${parsed.protocol}//${parsed.hostname}`,
    suggestedName: name,
    platformType: platform,
  };
}

function detectPlatformFromHostname(hostname: string, url: string): PlatformType {
  if (hostname.includes("myshopify.com")) return "shopify";
  if (url.includes("/wp-json/wc/") || url.includes("woocommerce")) return "woocommerce";
  // Shopify pattern: stores that use Shopify CDN or have /collections/ paths
  // This is heuristic — platform can be confirmed after first crawl
  return "unknown";
}
```

## `frontend/src/hooks/useCreateMerchant.ts`
```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import { useNavigate } from "@tanstack/react-router";

interface CreateMerchantInput {
  name: string;
  canonical_domain: string;
  homepage_url: string;
  platform_type: string;
  country_code?: string;
  auto_crawl?: boolean;
}

export function useCreateMerchant() {
  const qc = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async (input: CreateMerchantInput) => {
      // 1. Create merchant
      const { data: merchant, error } = await api.POST("/api/v1/merchants", {
        body: {
          name: input.name,
          canonical_domain: input.canonical_domain,
          homepage_url: input.homepage_url,
          platform_type: input.platform_type,
          country_code: input.country_code ?? "US",
        },
      });
      if (error) throw error;

      // 2. Trigger crawl if requested
      if (input.auto_crawl && merchant) {
        await api.POST("/api/v1/merchants/{merchant_id}/crawl", {
          params: { path: { merchant_id: merchant.id } },
        });
      }
      return merchant;
    },
    onSuccess: (merchant) => {
      qc.invalidateQueries({ queryKey: ["merchants"] });
      if (merchant) navigate({ to: "/merchants/$id", params: { id: String(merchant.id) } });
    },
  });
}
```

## `frontend/src/routes/merchants.new.tsx`
```tsx
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useCreateMerchant } from "@/hooks/useCreateMerchant";
import { detectPlatform } from "@/lib/platform-detect";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export const Route = createFileRoute("/merchants/new")({
  component: AddMerchantPage,
});

function AddMerchantPage() {
  const [url, setUrl] = useState("");
  const [name, setName] = useState("");
  const [platform, setPlatform] = useState("unknown");
  const [autoCrawl, setAutoCrawl] = useState(true);
  const { mutate, isPending, error } = useCreateMerchant();

  const preview = url ? detectPlatform(url) : null;

  const handleUrlChange = (v: string) => {
    setUrl(v);
    if (v) {
      const p = detectPlatform(v);
      setName(p.suggestedName);
      setPlatform(p.platformType);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!preview) return;
    mutate({
      name,
      canonical_domain: preview.canonicalDomain,
      homepage_url: preview.homepageUrl,
      platform_type: platform,
      auto_crawl: autoCrawl,
    });
  };

  return (
    <div className="max-w-lg">
      <h1 className="text-2xl font-bold mb-6">🏪 Add Merchant</h1>
      <Card>
        <CardHeader><CardTitle>Store URL</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              placeholder="https://store.myshopify.com"
              value={url}
              onChange={(e) => handleUrlChange(e.target.value)}
            />

            {preview?.canonicalDomain && (
              <>
                <div>
                  <label className="text-sm font-medium">Store Name</label>
                  <Input value={name} onChange={(e) => setName(e.target.value)} />
                </div>
                <div>
                  <label className="text-sm font-medium">Platform</label>
                  <Select value={platform} onValueChange={setPlatform}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="shopify">Shopify</SelectItem>
                      <SelectItem value="woocommerce">WooCommerce</SelectItem>
                      <SelectItem value="agentic">Agentic</SelectItem>
                      <SelectItem value="unknown">Unknown</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="text-sm text-muted-foreground">
                  Domain: <strong>{preview.canonicalDomain}</strong>
                </div>
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={autoCrawl} onChange={(e) => setAutoCrawl(e.target.checked)} />
                  Trigger crawl immediately after adding
                </label>
              </>
            )}

            {error && <p className="text-red-600 text-sm">{String(error)}</p>}

            <Button type="submit" disabled={isPending || !preview?.canonicalDomain}>
              {isPending ? "Adding..." : "Add Merchant"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
```
