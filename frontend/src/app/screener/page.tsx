"use client";

import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { RefreshCw, AlertCircle } from "lucide-react";

import { FilterPanel } from "./_components/FilterPanel";
import { StockTable } from "./_components/StockTable";
import { useScreener } from "./_hooks/useScreener";

/**
 * スクリーナーページ
 */
export default function ScreenerPage() {
  const {
    data,
    sortedStocks,
    isLoading,
    error,
    filter,
    setFilter,
    resetFilter,
    sortKey,
    sortOrder,
    setSort,
    refetch,
  } = useScreener();

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="mx-auto max-w-7xl px-4 py-8">
        {/* ページヘッダー */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-foreground">
                CAN-SLIM スクリーナー
              </h1>
              <p className="text-sm text-muted-foreground mt-1">
                CAN-SLIM条件を満たす銘柄をスクリーニング
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={refetch}
              disabled={isLoading}
              className="gap-2"
            >
              <RefreshCw
                className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`}
              />
              更新
            </Button>
          </div>

          {/* 最終更新時刻 */}
          {data?.screened_at && (
            <p className="text-xs text-muted-foreground mt-2">
              最終スクリーニング:{" "}
              {new Date(data.screened_at).toLocaleString("ja-JP")}
            </p>
          )}
        </div>

        {/* エラー表示 */}
        {error && (
          <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <div>
              <p className="font-medium text-destructive">エラーが発生しました</p>
              <p className="text-sm text-destructive/80">{error}</p>
            </div>
          </div>
        )}

        {/* メインコンテンツ */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* フィルターパネル（サイドバー） */}
          <div className="lg:col-span-1">
            <FilterPanel
              filter={filter}
              onFilterChange={setFilter}
              onReset={resetFilter}
              isLoading={isLoading}
            />
          </div>

          {/* 銘柄テーブル（メイン） */}
          <div className="lg:col-span-3">
            <StockTable
              stocks={sortedStocks}
              sortKey={sortKey}
              sortOrder={sortOrder}
              onSort={setSort}
              isLoading={isLoading}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
