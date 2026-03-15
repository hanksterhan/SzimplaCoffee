# SC-26 Execution Plan: Discovery Pipeline Page

## `frontend/src/hooks/useDiscovery.ts`
```typescript
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";

export function useDiscoveryCandidates(status = "pending") {
  return useQuery({
    queryKey: ["discovery", "candidates", status],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/discovery/candidates", {
        params: { query: { status } },
      });
      if (error) throw error;
      return data;
    },
    staleTime: 30_000,
  });
}

export function usePromoteCandidate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (candidateId: number) => {
      const { data, error } = await api.POST(
        "/api/v1/discovery/candidates/{candidate_id}/promote",
        { params: { path: { candidate_id: candidateId } } }
      );
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["discovery"] });
      qc.invalidateQueries({ queryKey: ["merchants"] });
    },
  });
}

export function useRejectCandidate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (candidateId: number) => {
      const { data, error } = await api.POST(
        "/api/v1/discovery/candidates/{candidate_id}/reject",
        { params: { path: { candidate_id: candidateId } } }
      );
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["discovery", "candidates"] });
    },
  });
}

export function useRunDiscovery() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (query = "specialty coffee roaster") => {
      const { data, error } = await api.POST("/api/v1/discovery/run", {
        params: { query: { query } },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      setTimeout(() => qc.invalidateQueries({ queryKey: ["discovery"] }), 3000);
    },
  });
}
```

## `frontend/src/components/discovery/CandidateCard.tsx`
```tsx
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { MerchantCandidateSchema } from "@/api";
import { Link } from "@tanstack/react-router";

interface CandidateCardProps {
  candidate: MerchantCandidateSchema;
  onPromote: (id: number) => void;
  onReject: (id: number) => void;
  isPromoting: boolean;
  isRejecting: boolean;
  promotedMerchantId?: number;
}

export function CandidateCard({
  candidate,
  onPromote,
  onReject,
  isPromoting,
  isRejecting,
  promotedMerchantId,
}: CandidateCardProps) {
  const confidencePct = Math.round(candidate.confidence * 100);

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-semibold">{candidate.merchant_name}</p>
            <a
              href={candidate.homepage_url}
              target="_blank"
              rel="noreferrer"
              className="text-sm text-blue-600 hover:underline"
            >
              {candidate.canonical_domain}
            </a>
          </div>
          <div className="text-right">
            <Badge variant="outline" className="capitalize">{candidate.platform_type}</Badge>
            <p className="text-xs text-muted-foreground mt-1">
              {confidencePct}% confidence
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {candidate.notes && (
          <p className="text-sm text-muted-foreground mb-3">{candidate.notes}</p>
        )}
        {candidate.status === "pending" && (
          <div className="flex gap-2">
            <Button
              size="sm"
              onClick={() => onPromote(candidate.id)}
              disabled={isPromoting}
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              ✓ Promote
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => onReject(candidate.id)}
              disabled={isRejecting}
              className="text-red-600 border-red-200"
            >
              ✗ Reject
            </Button>
          </div>
        )}
        {candidate.status === "approved" && promotedMerchantId && (
          <Link to="/merchants/$id" params={{ id: String(promotedMerchantId) }}>
            <Button size="sm" variant="outline">View Merchant →</Button>
          </Link>
        )}
      </CardContent>
    </Card>
  );
}
```

## `frontend/src/routes/discovery.tsx`
```tsx
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { useDiscoveryCandidates, usePromoteCandidate, useRejectCandidate, useRunDiscovery } from "@/hooks/useDiscovery";
import { CandidateCard } from "@/components/discovery/CandidateCard";

export const Route = createFileRoute("/discovery")({
  component: DiscoveryPage,
});

function DiscoveryPage() {
  const [tab, setTab] = useState("pending");
  const { data: candidates = [], isLoading } = useDiscoveryCandidates(tab);
  const promote = usePromoteCandidate();
  const reject = useRejectCandidate();
  const runDiscovery = useRunDiscovery();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">🔍 Discovery</h1>
          <p className="text-muted-foreground">Review and promote merchant candidates</p>
        </div>
        <Button
          onClick={() => runDiscovery.mutate()}
          disabled={runDiscovery.isPending}
        >
          {runDiscovery.isPending ? "Searching..." : "🔍 Run Discovery"}
        </Button>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="pending">Pending</TabsTrigger>
          <TabsTrigger value="approved">Approved</TabsTrigger>
          <TabsTrigger value="rejected">Rejected</TabsTrigger>
        </TabsList>
        <TabsContent value={tab}>
          {isLoading ? (
            <p className="text-muted-foreground py-8 text-center">Loading candidates...</p>
          ) : candidates.length === 0 ? (
            <p className="text-muted-foreground py-8 text-center">
              No {tab} candidates. {tab === "pending" && "Run discovery to find new merchants."}
            </p>
          ) : (
            <div className="grid gap-3 mt-4">
              {candidates.map((c: any) => (
                <CandidateCard
                  key={c.id}
                  candidate={c}
                  onPromote={(id) => promote.mutate(id)}
                  onReject={(id) => reject.mutate(id)}
                  isPromoting={promote.isPending}
                  isRejecting={reject.isPending}
                />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
```
