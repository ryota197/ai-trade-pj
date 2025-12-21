"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { OpenTradeRequest, TradeType } from "@/types/portfolio";

interface TradeFormProps {
  onSubmit: (data: OpenTradeRequest) => Promise<void>;
  isSubmitting?: boolean;
}

/**
 * 新規トレードフォームコンポーネント
 */
export function TradeForm({ onSubmit, isSubmitting = false }: TradeFormProps) {
  const [symbol, setSymbol] = useState("");
  const [tradeType, setTradeType] = useState<TradeType>("buy");
  const [quantity, setQuantity] = useState("");
  const [entryPrice, setEntryPrice] = useState("");
  const [stopLossPrice, setStopLossPrice] = useState("");
  const [targetPrice, setTargetPrice] = useState("");
  const [notes, setNotes] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const data: OpenTradeRequest = {
      symbol: symbol.toUpperCase(),
      trade_type: tradeType,
      quantity: parseInt(quantity),
      entry_price: parseFloat(entryPrice),
      stop_loss_price: stopLossPrice ? parseFloat(stopLossPrice) : undefined,
      target_price: targetPrice ? parseFloat(targetPrice) : undefined,
      notes: notes || undefined,
    };

    await onSubmit(data);

    // Reset form
    setSymbol("");
    setQuantity("");
    setEntryPrice("");
    setStopLossPrice("");
    setTargetPrice("");
    setNotes("");
  };

  const isValid =
    symbol.trim() !== "" &&
    quantity !== "" &&
    parseInt(quantity) > 0 &&
    entryPrice !== "" &&
    parseFloat(entryPrice) > 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle>New Trade</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Symbol & Type */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Symbol</label>
              <input
                type="text"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                className="w-full px-3 py-2 border rounded-md bg-background"
                placeholder="AAPL"
                maxLength={10}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Type</label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setTradeType("buy")}
                  className={`flex-1 py-2 rounded-md font-medium transition-colors ${
                    tradeType === "buy"
                      ? "bg-green-500 text-white"
                      : "bg-muted hover:bg-muted/80"
                  }`}
                >
                  BUY
                </button>
                <button
                  type="button"
                  onClick={() => setTradeType("sell")}
                  className={`flex-1 py-2 rounded-md font-medium transition-colors ${
                    tradeType === "sell"
                      ? "bg-red-500 text-white"
                      : "bg-muted hover:bg-muted/80"
                  }`}
                >
                  SELL
                </button>
              </div>
            </div>
          </div>

          {/* Quantity & Entry Price */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Quantity</label>
              <input
                type="number"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                className="w-full px-3 py-2 border rounded-md bg-background"
                placeholder="100"
                min="1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Entry Price
              </label>
              <input
                type="number"
                step="0.01"
                value={entryPrice}
                onChange={(e) => setEntryPrice(e.target.value)}
                className="w-full px-3 py-2 border rounded-md bg-background"
                placeholder="150.00"
                min="0.01"
              />
            </div>
          </div>

          {/* Stop Loss & Target */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                Stop Loss (Optional)
              </label>
              <input
                type="number"
                step="0.01"
                value={stopLossPrice}
                onChange={(e) => setStopLossPrice(e.target.value)}
                className="w-full px-3 py-2 border rounded-md bg-background"
                placeholder="145.00"
                min="0.01"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Target Price (Optional)
              </label>
              <input
                type="number"
                step="0.01"
                value={targetPrice}
                onChange={(e) => setTargetPrice(e.target.value)}
                className="w-full px-3 py-2 border rounded-md bg-background"
                placeholder="165.00"
                min="0.01"
              />
            </div>
          </div>

          {/* Position Value Preview */}
          {quantity && entryPrice && (
            <div className="p-3 bg-muted/50 rounded-md">
              <p className="text-sm text-muted-foreground">
                Position Value:{" "}
                <span className="font-medium text-foreground">
                  ${(parseInt(quantity) * parseFloat(entryPrice)).toFixed(2)}
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
              placeholder="Entry reason, strategy..."
              rows={2}
              maxLength={1000}
            />
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            className="w-full"
            disabled={!isValid || isSubmitting}
          >
            {isSubmitting ? "Opening Position..." : "Open Position"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
