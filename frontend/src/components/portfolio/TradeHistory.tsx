"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { Trade, TradeStatus } from "@/types/portfolio";

interface TradeHistoryProps {
  trades: Trade[];
  isLoading?: boolean;
  onClose?: (tradeId: number, exitPrice: number) => Promise<void>;
  onCancel?: (tradeId: number) => Promise<void>;
}

/**
 * トレード履歴テーブルコンポーネント
 */
export function TradeHistory({
  trades,
  isLoading = false,
  onClose,
  onCancel,
}: TradeHistoryProps) {
  const [closingId, setClosingId] = useState<number | null>(null);
  const [cancellingId, setCancellingId] = useState<number | null>(null);
  const [closePrice, setClosePrice] = useState<string>("");
  const [showCloseModal, setShowCloseModal] = useState<number | null>(null);

  const handleClose = async (tradeId: number) => {
    if (!onClose || !closePrice) return;
    setClosingId(tradeId);
    try {
      await onClose(tradeId, parseFloat(closePrice));
      setShowCloseModal(null);
      setClosePrice("");
    } finally {
      setClosingId(null);
    }
  };

  const handleCancel = async (tradeId: number) => {
    if (!onCancel) return;
    setCancellingId(tradeId);
    try {
      await onCancel(tradeId);
    } finally {
      setCancellingId(null);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const formatPrice = (price: number | null) => {
    if (price === null) return "-";
    return `$${price.toFixed(2)}`;
  };

  const getStatusBadge = (status: TradeStatus) => {
    const styles: Record<TradeStatus, string> = {
      open: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
      closed:
        "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
      cancelled: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300",
    };
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded ${styles[status]}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  const getTypeBadge = (type: string) => {
    return type === "buy" ? (
      <span className="text-green-500 font-medium">BUY</span>
    ) : (
      <span className="text-red-500 font-medium">SELL</span>
    );
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Trade History</CardTitle>
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

  if (trades.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Trade History</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">
            No trades yet. Start paper trading to track your performance.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Trade History ({trades.length})</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-3 px-2 font-medium">Symbol</th>
                <th className="text-left py-3 px-2 font-medium">Type</th>
                <th className="text-right py-3 px-2 font-medium">Qty</th>
                <th className="text-right py-3 px-2 font-medium">Entry</th>
                <th className="text-right py-3 px-2 font-medium">Exit</th>
                <th className="text-right py-3 px-2 font-medium">P/L</th>
                <th className="text-right py-3 px-2 font-medium">Return</th>
                <th className="text-left py-3 px-2 font-medium">Status</th>
                <th className="text-right py-3 px-2 font-medium">Days</th>
                <th className="text-right py-3 px-2 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((trade) => (
                <tr
                  key={trade.id}
                  className="border-b hover:bg-muted/50 transition-colors"
                >
                  <td className="py-3 px-2">
                    <div>
                      <span className="font-medium">{trade.symbol}</span>
                      <div className="text-xs text-muted-foreground">
                        {formatDate(trade.entry_date)}
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-2">{getTypeBadge(trade.trade_type)}</td>
                  <td className="py-3 px-2 text-right">{trade.quantity}</td>
                  <td className="py-3 px-2 text-right">
                    {formatPrice(trade.entry_price)}
                  </td>
                  <td className="py-3 px-2 text-right">
                    {formatPrice(trade.exit_price)}
                  </td>
                  <td
                    className={`py-3 px-2 text-right font-medium ${
                      trade.profit_loss !== null
                        ? trade.profit_loss >= 0
                          ? "text-green-500"
                          : "text-red-500"
                        : ""
                    }`}
                  >
                    {trade.profit_loss !== null
                      ? `${trade.profit_loss >= 0 ? "+" : ""}$${trade.profit_loss.toFixed(2)}`
                      : "-"}
                  </td>
                  <td
                    className={`py-3 px-2 text-right ${
                      trade.return_percent !== null
                        ? trade.return_percent >= 0
                          ? "text-green-500"
                          : "text-red-500"
                        : ""
                    }`}
                  >
                    {trade.return_percent !== null
                      ? `${trade.return_percent >= 0 ? "+" : ""}${trade.return_percent.toFixed(2)}%`
                      : "-"}
                  </td>
                  <td className="py-3 px-2">{getStatusBadge(trade.status)}</td>
                  <td className="py-3 px-2 text-right text-muted-foreground">
                    {trade.holding_days ?? "-"}
                  </td>
                  <td className="py-3 px-2 text-right">
                    {trade.status === "open" && (
                      <div className="flex justify-end gap-2">
                        {onClose && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setShowCloseModal(trade.id)}
                          >
                            Close
                          </Button>
                        )}
                        {onCancel && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-red-500"
                            onClick={() => handleCancel(trade.id)}
                            disabled={cancellingId === trade.id}
                          >
                            {cancellingId === trade.id ? "..." : "Cancel"}
                          </Button>
                        )}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Close Modal */}
        {showCloseModal !== null && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-background p-6 rounded-lg shadow-lg w-full max-w-md">
              <h3 className="text-lg font-semibold mb-4">Close Position</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Exit Price
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={closePrice}
                    onChange={(e) => setClosePrice(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md bg-background"
                    placeholder="Enter exit price"
                  />
                </div>
                <div className="flex justify-end gap-2">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setShowCloseModal(null);
                      setClosePrice("");
                    }}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={() => handleClose(showCloseModal)}
                    disabled={!closePrice || closingId === showCloseModal}
                  >
                    {closingId === showCloseModal ? "Closing..." : "Close Trade"}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
