"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { StockDetail } from "@/types/stock";

interface StockHeaderProps {
  stock: StockDetail;
}

export function StockHeader({ stock }: StockHeaderProps) {
  const changePercent = stock.change_percent ?? 0;
  const isPositive = changePercent >= 0;

  return (
    <div className="space-y-4">
      {/* 戻るリンク */}
      <Link
        href="/screener"
        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
      >
        <ArrowLeft className="h-4 w-4" />
        スクリーナーに戻る
      </Link>

      {/* 銘柄情報 */}
      <div className="flex items-baseline gap-4">
        <h1 className="text-3xl font-bold">{stock.symbol}</h1>
        <span className="text-lg text-gray-600">{stock.name}</span>
      </div>

      {/* 価格と変動率 */}
      <div className="flex items-baseline gap-4">
        <span className="text-4xl font-semibold">
          ${(stock.price ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
        </span>
        <span
          className={`text-xl font-medium ${
            isPositive ? "text-green-600" : "text-red-600"
          }`}
        >
          {isPositive ? "+" : ""}
          {changePercent.toFixed(2)}%
        </span>
      </div>

      {/* 更新日時 */}
      <p className="text-sm text-gray-500">
        最終更新: {new Date(stock.updated_at).toLocaleString("ja-JP")}
      </p>
    </div>
  );
}
