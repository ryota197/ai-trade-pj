"use client";

import { useState } from "react";
import { Play, Loader2, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import type { SymbolSource } from "@/types/admin";
import { useAdminRefresh } from "../_hooks/useAdminRefresh";
import { useFlowHistory } from "../_hooks/useFlowHistory";
import { FlowProgress } from "./FlowProgress";

const SOURCE_OPTIONS: {
  value: SymbolSource;
  label: string;
  description: string;
}[] = [
  {
    value: "sp500",
    label: "S&P 500",
    description: "S&P 500構成銘柄 (約500銘柄)",
  },
  {
    value: "nasdaq100",
    label: "NASDAQ 100",
    description: "NASDAQ 100構成銘柄 (約100銘柄)",
  },
];

/**
 * スクリーニングデータ更新パネル
 */
export function RefreshPanel() {
  const [selectedSource, setSelectedSource] =
    useState<SymbolSource>("nasdaq100");
  const { isLoading, error, startRefresh } = useAdminRefresh();
  const { flows, refresh: refreshHistory, isLoading: isLoadingHistory } = useFlowHistory(1);
  const latestFlow = flows[0] ?? null;

  const handleStart = async () => {
    await startRefresh(selectedSource);
    // 開始後に履歴を再取得
    refreshHistory();
  };

  const handleRefreshStatus = () => {
    refreshHistory();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>スクリーニングデータ更新</CardTitle>
        <CardDescription>
          指定されたシンボルリストの銘柄データを更新します。
          更新はバックグラウンドで実行されます。
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* ソース選択 */}
        <div className="space-y-3">
          <label className="text-sm font-medium">更新対象</label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {SOURCE_OPTIONS.map((option) => (
              <button
                key={option.value}
                onClick={() => setSelectedSource(option.value)}
                disabled={isLoading}
                className={`p-4 rounded-lg border text-left transition-colors ${
                  selectedSource === option.value
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-muted-foreground/50"
                } ${isLoading ? "opacity-50 cursor-not-allowed" : ""}`}
              >
                <div className="font-medium">{option.label}</div>
                <div className="text-sm text-muted-foreground mt-1">
                  {option.description}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* アクションボタン */}
        <div className="flex items-center gap-3">
          <Button onClick={handleStart} disabled={isLoading} className="gap-2">
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            {isLoading ? "開始中..." : "更新開始"}
          </Button>
          {latestFlow && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefreshStatus}
              disabled={isLoadingHistory}
              className="gap-2"
            >
              <RefreshCw
                className={`h-4 w-4 ${isLoadingHistory ? "animate-spin" : ""}`}
              />
              状態更新
            </Button>
          )}
        </div>

        {/* エラー表示 */}
        {error && (
          <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
            <p className="text-sm text-destructive">{error}</p>
          </div>
        )}

        {/* 最新フローの進捗表示 */}
        {latestFlow && <FlowProgress status={latestFlow} />}
      </CardContent>
    </Card>
  );
}
