import { useMerchantProducts } from "@/hooks/use-merchants";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

interface ProductsTabProps {
  merchantId: number;
}

export function ProductsTab({ merchantId }: ProductsTabProps) {
  const { data, isLoading } = useMerchantProducts(merchantId, 100);

  if (isLoading) {
    return (
      <div className="space-y-2 mt-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    );
  }

  if (!data?.items.length) {
    return (
      <div className="py-12 text-center text-muted-foreground">
        No products found for this merchant.
      </div>
    );
  }

  return (
    <div className="mt-4 space-y-2">
      <p className="text-sm text-muted-foreground">
        {data.total} products ({data.items.filter((p) => p.is_active).length} active)
      </p>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12"></TableHead>
            <TableHead>Name</TableHead>
            <TableHead>Origin</TableHead>
            <TableHead>Process</TableHead>
            <TableHead>Espresso</TableHead>
            <TableHead>Active</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.items.map((p) => (
            <TableRow key={p.id}>
              <TableCell>
                {p.image_url ? (
                  <img
                    src={p.image_url}
                    alt={p.name}
                    className="w-8 h-8 object-cover rounded"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = "none";
                    }}
                  />
                ) : (
                  <div className="w-8 h-8 bg-muted rounded flex items-center justify-center text-xs">
                    ☕
                  </div>
                )}
              </TableCell>
              <TableCell>
                <a
                  href={p.product_url}
                  target="_blank"
                  rel="noreferrer"
                  className="font-medium hover:underline text-blue-600 text-sm"
                >
                  {p.name}
                </a>
              </TableCell>
              <TableCell className="text-sm text-muted-foreground max-w-32 truncate">
                {p.origin_text || "—"}
              </TableCell>
              <TableCell className="text-sm text-muted-foreground max-w-32 truncate">
                {p.process_text || "—"}
              </TableCell>
              <TableCell>
                {p.is_espresso_recommended && (
                  <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200 text-xs">
                    ☕ Espresso
                  </Badge>
                )}
              </TableCell>
              <TableCell>
                <span className={`text-sm ${p.is_active ? "text-green-600" : "text-gray-400"}`}>
                  {p.is_active ? "✓" : "—"}
                </span>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
