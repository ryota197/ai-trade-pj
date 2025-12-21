"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { WatchlistItem } from "@/types/portfolio";

interface WatchlistTableProps {
  items: WatchlistItem[];
  isLoading?: boolean;
  onRemove?: (symbol: string) => Promise<void>;
  onEdit?: (item: WatchlistItem) => void;
}

/**
 * ウォッチリストテーブルコンポーネント
 */
export function WatchlistTable({
  items,
  isLoading = false,
  onRemove,
  onEdit,
}: WatchlistTableProps) {
  const [removingSymbol, setRemovingSymbol] = useState<string | null>(null);

  const handleRemove = async (symbol: string) => {
    if (!onRemove) return;
    setRemovingSymbol(symbol);
    try {
      await onRemove(symbol);
    } finally {
      setRemovingSymbol(null);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const formatPrice = (price: number | null) => {
    if (price === null) return "-";
    return `$${price.toFixed(2)}`;
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      watching: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
      triggered:
        "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
      expired:
        "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300",
      removed: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
    };
    return (
      <span
        className={`px-2 py-1 text-xs font-medium rounded ${styles[status] || styles.watching}`}
      >
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Watchlist</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-muted rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (items.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Watchlist</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">
            No stocks in watchlist. Add stocks to track them.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Watchlist ({items.length})</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-3 px-2 font-medium">Symbol</th>
                <th className="text-left py-3 px-2 font-medium">Status</th>
                <th className="text-right py-3 px-2 font-medium">Entry</th>
                <th className="text-right py-3 px-2 font-medium">Stop Loss</th>
                <th className="text-right py-3 px-2 font-medium">Target</th>
                <th className="text-right py-3 px-2 font-medium">R/R</th>
                <th className="text-left py-3 px-2 font-medium">Added</th>
                <th className="text-right py-3 px-2 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr
                  key={item.id}
                  className="border-b hover:bg-muted/50 transition-colors"
                >
                  <td className="py-3 px-2">
                    <span className="font-medium">{item.symbol}</span>
                  </td>
                  <td className="py-3 px-2">{getStatusBadge(item.status)}</td>
                  <td className="py-3 px-2 text-right">
                    {formatPrice(item.target_entry_price)}
                  </td>
                  <td className="py-3 px-2 text-right text-red-500">
                    {formatPrice(item.stop_loss_price)}
                  </td>
                  <td className="py-3 px-2 text-right text-green-500">
                    {formatPrice(item.target_price)}
                  </td>
                  <td className="py-3 px-2 text-right">
                    {item.risk_reward_ratio
                      ? `${item.risk_reward_ratio.toFixed(2)}`
                      : "-"}
                  </td>
                  <td className="py-3 px-2 text-muted-foreground">
                    {formatDate(item.added_at)}
                  </td>
                  <td className="py-3 px-2 text-right">
                    <div className="flex justify-end gap-2">
                      {onEdit && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onEdit(item)}
                        >
                          Edit
                        </Button>
                      )}
                      {onRemove && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-red-500 hover:text-red-700"
                          onClick={() => handleRemove(item.symbol)}
                          disabled={removingSymbol === item.symbol}
                        >
                          {removingSymbol === item.symbol
                            ? "Removing..."
                            : "Remove"}
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* ノート表示 */}
        {items.some((item) => item.notes) && (
          <div className="mt-4 space-y-2">
            <p className="text-sm font-medium text-muted-foreground">Notes:</p>
            {items
              .filter((item) => item.notes)
              .map((item) => (
                <div
                  key={item.id}
                  className="text-sm p-2 bg-muted/50 rounded"
                >
                  <span className="font-medium">{item.symbol}:</span>{" "}
                  {item.notes}
                </div>
              ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
