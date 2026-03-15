import { useMerchantCrawlRuns } from "@/hooks/use-merchants";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { CrawlStatusBadge } from "./CrawlStatusBadge";
import { Skeleton } from "@/components/ui/skeleton";

interface CrawlRunsTabProps {
  merchantId: number;
}

function formatDuration(seconds: number | null): string {
  if (seconds === null) return "—";
  if (seconds < 60) return `${Math.round(seconds)}s`;
  return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
}

export function CrawlRunsTab({ merchantId }: CrawlRunsTabProps) {
  const { data, isLoading } = useMerchantCrawlRuns(merchantId);

  if (isLoading) {
    return (
      <div className="space-y-2 mt-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    );
  }

  if (!data?.length) {
    return (
      <div className="py-12 text-center text-muted-foreground">
        No crawl runs found.
      </div>
    );
  }

  return (
    <div className="mt-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Started</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Adapter</TableHead>
            <TableHead>Records</TableHead>
            <TableHead>Duration</TableHead>
            <TableHead>Errors</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((run) => (
            <TableRow key={run.id}>
              <TableCell className="text-sm">
                {new Date(run.started_at).toLocaleString()}
              </TableCell>
              <TableCell>
                <CrawlStatusBadge status={run.status} />
              </TableCell>
              <TableCell className="text-sm font-mono text-muted-foreground">
                {run.adapter_name}
              </TableCell>
              <TableCell className="text-sm font-medium">
                {run.records_written}
              </TableCell>
              <TableCell className="text-sm">
                {formatDuration(run.duration_seconds)}
              </TableCell>
              <TableCell className="text-sm text-red-600 max-w-48 truncate" title={run.error_summary}>
                {run.error_summary || "—"}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
