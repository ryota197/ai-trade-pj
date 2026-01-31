"use client";

import Link from "next/link";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight } from "lucide-react";
import { useTopStocks } from "../_hooks/useTopStocks";

/**
 * Top CAN-SLIM銘柄カード
 *
 * ダッシュボードにCAN-SLIMスコア上位5銘柄を表示
 */
export function TopStocksCard() {
  const { stocks, isLoading, error } = useTopStocks(5);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Top CAN-SLIM Stocks</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-10 bg-muted rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || stocks.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Top CAN-SLIM Stocks</CardTitle>
        </CardHeader>
        <CardContent className="py-8 text-center text-muted-foreground">
          スクリーニングデータがありません
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Top CAN-SLIM Stocks</CardTitle>
        <Link
          href="/screener"
          className="text-sm text-primary hover:underline flex items-center gap-1"
        >
          すべて見る <ArrowRight className="h-4 w-4" />
        </Link>
      </CardHeader>
      <CardContent>
        <table className="w-full">
          <thead>
            <tr className="text-xs text-muted-foreground border-b">
              <th className="text-left py-2">Symbol</th>
              <th className="text-right py-2">Price</th>
              <th className="text-right py-2">Change</th>
              <th className="text-right py-2">RS</th>
              <th className="text-right py-2">Score</th>
            </tr>
          </thead>
          <tbody>
            {stocks.map((stock) => (
              <tr key={stock.symbol} className="border-b last:border-0">
                <td className="py-3">
                  <Link
                    href={`/stock/${stock.symbol}`}
                    className="font-mono font-bold text-primary hover:underline"
                  >
                    {stock.symbol}
                  </Link>
                </td>
                <td className="text-right font-mono">
                  ${stock.price.toFixed(2)}
                </td>
                <td
                  className={`text-right font-mono ${
                    stock.change_percent >= 0
                      ? "text-green-600"
                      : "text-red-600"
                  }`}
                >
                  {stock.change_percent >= 0 ? "+" : ""}
                  {stock.change_percent.toFixed(2)}%
                </td>
                <td className="text-right">
                  <Badge variant="secondary">{stock.rs_rating}</Badge>
                </td>
                <td className="text-right">
                  <Badge>{stock.canslim_score}</Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
