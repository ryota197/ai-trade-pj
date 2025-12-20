"use client";

import { use } from "react";
import Link from "next/link";
import { ArrowLeft, RefreshCw, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PriceChart } from "@/components/charts/PriceChart";
import { FundamentalsCard, CANSLIMScoreCard } from "@/components/stock";
import { useStockData } from "@/hooks/useStockData";

interface StockDetailPageProps {
  params: Promise<{ symbol: string }>;
}

export default function StockDetailPage({ params }: StockDetailPageProps) {
  const { symbol } = use(params);
  const upperSymbol = symbol.toUpperCase();

  const { quote, priceHistory, financials, isLoading, error, refetch } =
    useStockData(upperSymbol);

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center gap-4 mb-8">
          <Link href="/screener">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              スクリーナーに戻る
            </Button>
          </Link>
        </div>
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
          <p className="text-lg font-medium text-red-600">エラーが発生しました</p>
          <p className="text-sm mt-1">{error}</p>
          <Button onClick={refetch} className="mt-4">
            再試行
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* ヘッダー */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <Link href="/screener">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              スクリーナー
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold font-mono">{upperSymbol}</h1>
              {quote && (
                <Badge
                  variant={quote.change_percent >= 0 ? "default" : "destructive"}
                  className="text-lg px-3 py-1"
                >
                  {quote.change_percent >= 0 ? "+" : ""}
                  {quote.change_percent.toFixed(2)}%
                </Badge>
              )}
            </div>
            {quote && (
              <p className="text-muted-foreground mt-1">
                最終更新: {new Date(quote.timestamp).toLocaleString("ja-JP")}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={refetch}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
            更新
          </Button>
          <a
            href={`https://finance.yahoo.com/quote/${upperSymbol}`}
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button variant="outline" size="sm">
              <ExternalLink className="h-4 w-4 mr-2" />
              Yahoo Finance
            </Button>
          </a>
        </div>
      </div>

      {/* メインコンテンツ */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 左側: チャート */}
        <div className="lg:col-span-2">
          <PriceChart
            data={priceHistory}
            symbol={upperSymbol}
            isLoading={isLoading}
          />
        </div>

        {/* 右側: 財務指標 */}
        <div className="space-y-6">
          {quote && (
            <FundamentalsCard quote={quote} financials={financials} />
          )}
        </div>
      </div>

      {/* CAN-SLIMスコア（フルワイド） */}
      <div className="mt-6">
        <CANSLIMScoreCard score={null} isLoading={isLoading} />
      </div>
    </div>
  );
}
