"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { StockSummary, SortKey, SortOrder } from "@/types/stock";
import {
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  TrendingUp,
  TrendingDown,
  List,
} from "lucide-react";

interface StockTableProps {
  stocks: StockSummary[];
  sortKey: SortKey;
  sortOrder: SortOrder;
  onSort: (key: SortKey) => void;
  onStockClick?: (stock: StockSummary) => void;
  isLoading?: boolean;
}

interface SortableHeaderProps {
  label: string;
  sortKey: SortKey;
  currentSortKey: SortKey;
  sortOrder: SortOrder;
  onSort: (key: SortKey) => void;
  align?: "left" | "right";
}

function SortableHeader({
  label,
  sortKey,
  currentSortKey,
  sortOrder,
  onSort,
  align = "left",
}: SortableHeaderProps) {
  const isActive = sortKey === currentSortKey;

  return (
    <th
      className={`px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider cursor-pointer hover:text-foreground transition-colors ${
        align === "right" ? "text-right" : "text-left"
      }`}
      onClick={() => onSort(sortKey)}
    >
      <div
        className={`flex items-center gap-1 ${
          align === "right" ? "justify-end" : "justify-start"
        }`}
      >
        {label}
        {isActive ? (
          sortOrder === "asc" ? (
            <ArrowUp className="h-3 w-3" />
          ) : (
            <ArrowDown className="h-3 w-3" />
          )
        ) : (
          <ArrowUpDown className="h-3 w-3 opacity-30" />
        )}
      </div>
    </th>
  );
}

function getScoreBadgeVariant(
  score: number
): "default" | "secondary" | "destructive" | "outline" {
  if (score >= 90) return "default";
  if (score >= 70) return "secondary";
  if (score >= 50) return "outline";
  return "destructive";
}

function getRatingBadgeVariant(
  rating: number
): "default" | "secondary" | "destructive" | "outline" {
  if (rating >= 90) return "default";
  if (rating >= 80) return "secondary";
  if (rating >= 70) return "outline";
  return "destructive";
}

/**
 * 銘柄テーブル
 */
export function StockTable({
  stocks,
  sortKey,
  sortOrder,
  onSort,
  onStockClick,
  isLoading = false,
}: StockTableProps) {
  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-16">
          <div className="flex flex-col items-center justify-center text-muted-foreground">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-4" />
            <p>スクリーニング中...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (stocks.length === 0) {
    return (
      <Card>
        <CardContent className="py-16">
          <div className="flex flex-col items-center justify-center text-muted-foreground">
            <List className="h-12 w-12 mb-4 opacity-50" />
            <p className="text-lg font-medium">該当する銘柄がありません</p>
            <p className="text-sm mt-1">
              フィルター条件を緩和してお試しください
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="border-b">
        <div className="flex items-center justify-between">
          <CardTitle>スクリーニング結果</CardTitle>
          <Badge variant="outline">{stocks.length} 件</Badge>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr>
                <SortableHeader
                  label="シンボル"
                  sortKey="symbol"
                  currentSortKey={sortKey}
                  sortOrder={sortOrder}
                  onSort={onSort}
                />
                <SortableHeader
                  label="銘柄名"
                  sortKey="name"
                  currentSortKey={sortKey}
                  sortOrder={sortOrder}
                  onSort={onSort}
                />
                <SortableHeader
                  label="株価"
                  sortKey="price"
                  currentSortKey={sortKey}
                  sortOrder={sortOrder}
                  onSort={onSort}
                  align="right"
                />
                <SortableHeader
                  label="変動率"
                  sortKey="change_percent"
                  currentSortKey={sortKey}
                  sortOrder={sortOrder}
                  onSort={onSort}
                  align="right"
                />
                <SortableHeader
                  label="RS Rating"
                  sortKey="rs_rating"
                  currentSortKey={sortKey}
                  sortOrder={sortOrder}
                  onSort={onSort}
                  align="right"
                />
                <SortableHeader
                  label="CAN-SLIMスコア"
                  sortKey="canslim_score"
                  currentSortKey={sortKey}
                  sortOrder={sortOrder}
                  onSort={onSort}
                  align="right"
                />
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {stocks.map((stock) => (
                <tr
                  key={stock.symbol}
                  className="hover:bg-muted/30 transition-colors cursor-pointer"
                  onClick={() => onStockClick?.(stock)}
                >
                  <td className="px-4 py-3">
                    <span className="font-mono font-bold text-primary">
                      {stock.symbol}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm text-foreground truncate max-w-48 block">
                      {stock.name}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="font-mono">
                      ${stock.price.toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div
                      className={`flex items-center justify-end gap-1 font-mono ${
                        stock.change_percent >= 0
                          ? "text-green-600"
                          : "text-red-600"
                      }`}
                    >
                      {stock.change_percent >= 0 ? (
                        <TrendingUp className="h-3 w-3" />
                      ) : (
                        <TrendingDown className="h-3 w-3" />
                      )}
                      {stock.change_percent >= 0 ? "+" : ""}
                      {stock.change_percent.toFixed(2)}%
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Badge variant={getRatingBadgeVariant(stock.rs_rating)}>
                      {stock.rs_rating}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Badge variant={getScoreBadgeVariant(stock.canslim_score)}>
                      {stock.canslim_score}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
