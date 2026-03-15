import { createLazyFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  useDiscoveryCandidates,
  useRunDiscovery,
  usePromoteCandidate,
  useRejectCandidate,
  type MerchantCandidateSchema,
} from "@/hooks/use-discovery";

export const Route = createLazyFileRoute("/discovery")({
  component: DiscoveryPage,
});

// ─── helpers ─────────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  if (status === "approved") {
    return (
      <Badge className="bg-green-100 text-green-800 border-green-200 text-xs font-medium">
        ✓ Approved
      </Badge>
    );
  }
  if (status === "rejected") {
    return (
      <Badge className="bg-red-100 text-red-800 border-red-200 text-xs font-medium">
        ✗ Rejected
      </Badge>
    );
  }
  return (
    <Badge className="bg-blue-100 text-blue-800 border-blue-200 text-xs font-medium">
      ● Pending
    </Badge>
  );
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 80
      ? "bg-green-500"
      : pct >= 55
        ? "bg-amber-500"
        : "bg-red-400";
  return (
    <div className="flex items-center gap-2 text-xs">
      <div className="w-16 bg-muted rounded-full h-1.5 overflow-hidden">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-muted-foreground">{pct}%</span>
    </div>
  );
}

function CandidateCard({
  candidate,
  onPromote,
  onReject,
  promotingId,
  rejectingId,
}: {
  candidate: MerchantCandidateSchema;
  onPromote: (id: number) => void;
  onReject: (id: number) => void;
  promotingId: number | null;
  rejectingId: number | null;
}) {
  const isPromoting = promotingId === candidate.id;
  const isRejecting = rejectingId === candidate.id;
  const date = new Date(candidate.discovered_at).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <Card className="hover:shadow-sm transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <p className="font-semibold text-sm">{candidate.merchant_name}</p>
              <StatusBadge status={candidate.status} />
            </div>
            <div className="flex items-center gap-3 mt-1 flex-wrap">
              <a
                href={candidate.homepage_url}
                target="_blank"
                rel="noreferrer"
                className="text-xs text-blue-600 hover:underline"
              >
                {candidate.canonical_domain} ↗
              </a>
              <Badge variant="outline" className="text-xs capitalize">
                {candidate.platform_type}
              </Badge>
            </div>
          </div>
          <div className="text-right shrink-0">
            <ConfidenceBar value={candidate.confidence} />
            <p className="text-xs text-muted-foreground mt-1">{date}</p>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-muted-foreground">
          <div>
            <span className="font-medium text-foreground">Source: </span>
            {candidate.source_query}
          </div>
          {candidate.notes && (
            <div className="col-span-2">
              <span className="font-medium text-foreground">Notes: </span>
              {candidate.notes}
            </div>
          )}
        </div>

        {candidate.status === "pending" && (
          <div className="flex gap-2 pt-1">
            <Button
              size="sm"
              onClick={() => onPromote(candidate.id)}
              disabled={isPromoting || isRejecting}
              className="bg-green-700 hover:bg-green-800 text-white text-xs"
            >
              {isPromoting ? "Promoting…" : "✓ Promote"}
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => onReject(candidate.id)}
              disabled={isPromoting || isRejecting}
              className="text-red-600 border-red-200 hover:bg-red-50 text-xs"
            >
              {isRejecting ? "Rejecting…" : "✗ Reject"}
            </Button>
            <a
              href={candidate.homepage_url}
              target="_blank"
              rel="noreferrer"
              className="ml-auto"
            >
              <Button size="sm" variant="ghost" className="text-xs">
                View Site ↗
              </Button>
            </a>
          </div>
        )}

        {candidate.status !== "pending" && (
          <a
            href={candidate.homepage_url}
            target="_blank"
            rel="noreferrer"
          >
            <Button size="sm" variant="ghost" className="text-xs">
              View Site ↗
            </Button>
          </a>
        )}
      </CardContent>
    </Card>
  );
}

function CandidatesSkeleton() {
  return (
    <div className="space-y-3">
      {[0, 1, 2, 3].map((i) => (
        <Card key={i}>
          <CardHeader className="pb-2">
            <div className="flex justify-between">
              <div className="space-y-2 flex-1">
                <Skeleton className="h-4 w-40" />
                <Skeleton className="h-3 w-28" />
              </div>
              <Skeleton className="h-8 w-16" />
            </div>
          </CardHeader>
          <CardContent>
            <Skeleton className="h-3 w-full" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function CandidateList({
  status,
}: {
  status: string;
}) {
  const { data: candidates = [], isLoading } = useDiscoveryCandidates(status);
  const promote = usePromoteCandidate();
  const reject = useRejectCandidate();

  const [promotingId, setPromotingId] = useState<number | null>(null);
  const [rejectingId, setRejectingId] = useState<number | null>(null);

  function handlePromote(id: number) {
    setPromotingId(id);
    promote.mutate(id, {
      onSettled: () => setPromotingId(null),
    });
  }

  function handleReject(id: number) {
    setRejectingId(id);
    reject.mutate(id, {
      onSettled: () => setRejectingId(null),
    });
  }

  if (isLoading) return <CandidatesSkeleton />;

  if (candidates.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
        <span className="text-3xl mb-2">🔍</span>
        <p className="font-medium">No {status} candidates</p>
        {status === "pending" && (
          <p className="text-sm mt-1">
            Run discovery to find new specialty coffee merchants
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-3 mt-4">
      {candidates.map((c) => (
        <CandidateCard
          key={c.id}
          candidate={c}
          onPromote={handlePromote}
          onReject={handleReject}
          promotingId={promotingId}
          rejectingId={rejectingId}
        />
      ))}
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

function DiscoveryPage() {
  const [tab, setTab] = useState("pending");
  const runDiscovery = useRunDiscovery();

  const [discoveryQuery, setDiscoveryQuery] = useState(
    "specialty coffee roaster"
  );
  const [showQueryInput, setShowQueryInput] = useState(false);

  function handleRunDiscovery() {
    runDiscovery.mutate(discoveryQuery || undefined);
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 p-4 md:p-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">🔍 Discovery</h1>
          <p className="text-muted-foreground mt-1">
            Review and promote merchant candidates to your active merchant list
          </p>
        </div>

        <div className="flex flex-col items-end gap-2 shrink-0">
          <Button
            onClick={handleRunDiscovery}
            disabled={runDiscovery.isPending}
            className="bg-amber-800 hover:bg-amber-900 text-white"
          >
            {runDiscovery.isPending ? (
              <span className="flex items-center gap-2">
                <span className="animate-spin">⟳</span> Searching…
              </span>
            ) : (
              "🔍 Run Discovery"
            )}
          </Button>
          <button
            onClick={() => setShowQueryInput(!showQueryInput)}
            className="text-xs text-muted-foreground hover:underline"
          >
            {showQueryInput ? "Hide query" : "Customize query"}
          </button>
          {showQueryInput && (
            <input
              type="text"
              value={discoveryQuery}
              onChange={(e) => setDiscoveryQuery(e.target.value)}
              className="text-xs border border-border rounded px-2 py-1 w-52"
              placeholder="e.g. specialty coffee roaster"
            />
          )}
        </div>
      </div>

      {/* Discovery running notice */}
      {runDiscovery.isPending && (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="py-3 text-sm text-amber-800 flex items-center gap-2">
            <span className="animate-spin">⟳</span>
            Discovery running in the background for "{discoveryQuery}"… results
            will appear in a few moments.
          </CardContent>
        </Card>
      )}

      {runDiscovery.isSuccess && (
        <Card className="border-green-200 bg-green-50">
          <CardContent className="py-3 text-sm text-green-800">
            ✓ Discovery started for "{(runDiscovery.data as { query?: string })?.query ?? discoveryQuery}". New candidates will appear shortly.
          </CardContent>
        </Card>
      )}

      {runDiscovery.isError && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="py-3 text-sm text-red-700">
            ✗ Discovery failed:{" "}
            {(runDiscovery.error as Error)?.message ?? "Unknown error"}
          </CardContent>
        </Card>
      )}

      {/* Candidate tabs */}
      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="pending">Pending</TabsTrigger>
          <TabsTrigger value="approved">Approved</TabsTrigger>
          <TabsTrigger value="rejected">Rejected</TabsTrigger>
        </TabsList>

        <TabsContent value="pending">
          <CandidateList status="pending" />
        </TabsContent>
        <TabsContent value="approved">
          <CandidateList status="approved" />
        </TabsContent>
        <TabsContent value="rejected">
          <CandidateList status="rejected" />
        </TabsContent>
      </Tabs>
    </div>
  );
}
