"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import type { AddToWatchlistRequest } from "@/types/portfolio";

interface AddToWatchlistButtonProps {
  onAdd: (data: AddToWatchlistRequest) => Promise<void>;
  isAdding?: boolean;
}

/**
 * ウォッチリスト追加ボタン（モーダル付き）
 */
export function AddToWatchlistButton({
  onAdd,
  isAdding = false,
}: AddToWatchlistButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [symbol, setSymbol] = useState("");
  const [targetEntryPrice, setTargetEntryPrice] = useState("");
  const [stopLossPrice, setStopLossPrice] = useState("");
  const [targetPrice, setTargetPrice] = useState("");
  const [notes, setNotes] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const data: AddToWatchlistRequest = {
      symbol: symbol.toUpperCase(),
      target_entry_price: targetEntryPrice
        ? parseFloat(targetEntryPrice)
        : undefined,
      stop_loss_price: stopLossPrice ? parseFloat(stopLossPrice) : undefined,
      target_price: targetPrice ? parseFloat(targetPrice) : undefined,
      notes: notes || undefined,
    };

    await onAdd(data);
    resetForm();
    setIsOpen(false);
  };

  const resetForm = () => {
    setSymbol("");
    setTargetEntryPrice("");
    setStopLossPrice("");
    setTargetPrice("");
    setNotes("");
  };

  const isValid = symbol.trim() !== "";

  // Calculate R/R ratio preview
  const riskRewardRatio =
    targetEntryPrice && stopLossPrice && targetPrice
      ? (
          (parseFloat(targetPrice) - parseFloat(targetEntryPrice)) /
          (parseFloat(targetEntryPrice) - parseFloat(stopLossPrice))
        ).toFixed(2)
      : null;

  return (
    <>
      <Button onClick={() => setIsOpen(true)}>+ Add to Watchlist</Button>

      {isOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-background p-6 rounded-lg shadow-lg w-full max-w-md max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Add to Watchlist</h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Symbol */}
              <div>
                <label className="block text-sm font-medium mb-1">
                  Symbol *
                </label>
                <input
                  type="text"
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                  className="w-full px-3 py-2 border rounded-md bg-background"
                  placeholder="NVDA"
                  maxLength={10}
                  autoFocus
                />
              </div>

              {/* Target Entry Price */}
              <div>
                <label className="block text-sm font-medium mb-1">
                  Target Entry Price (Optional)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={targetEntryPrice}
                  onChange={(e) => setTargetEntryPrice(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md bg-background"
                  placeholder="440.00"
                  min="0.01"
                />
              </div>

              {/* Stop Loss & Target */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Stop Loss
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={stopLossPrice}
                    onChange={(e) => setStopLossPrice(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md bg-background"
                    placeholder="420.00"
                    min="0.01"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Target Price
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={targetPrice}
                    onChange={(e) => setTargetPrice(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md bg-background"
                    placeholder="500.00"
                    min="0.01"
                  />
                </div>
              </div>

              {/* R/R Ratio Preview */}
              {riskRewardRatio && (
                <div className="p-3 bg-muted/50 rounded-md">
                  <p className="text-sm text-muted-foreground">
                    Risk/Reward Ratio:{" "}
                    <span
                      className={`font-medium ${
                        parseFloat(riskRewardRatio) >= 2
                          ? "text-green-500"
                          : parseFloat(riskRewardRatio) >= 1
                            ? "text-yellow-500"
                            : "text-red-500"
                      }`}
                    >
                      1:{riskRewardRatio}
                    </span>
                  </p>
                </div>
              )}

              {/* Notes */}
              <div>
                <label className="block text-sm font-medium mb-1">
                  Notes (Optional)
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md bg-background resize-none"
                  placeholder="Entry reason, pattern detected..."
                  rows={3}
                  maxLength={1000}
                />
              </div>

              {/* Buttons */}
              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    resetForm();
                    setIsOpen(false);
                  }}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={!isValid || isAdding}>
                  {isAdding ? "Adding..." : "Add to Watchlist"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
