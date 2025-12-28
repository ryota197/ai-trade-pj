"use client";

import { useState } from "react";
import { Play, Loader2, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { useAdminRefresh } from "../_hooks/useAdminRefresh";

type SymbolSource = "sp500" | "nasdaq100";

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
 * スクリーニングデータ更新パネル（シンプル版）
 */
export function RefreshPanel() {
  const [selectedSource, setSelectedSource] =
    useState<SymbolSource>("nasdaq100");
  const { isLoading, error, lastJobId, startRefresh } = useAdminRefresh();

  const handleStart = () => {
    startRefresh(selectedSource);
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
        <Button onClick={handleStart} disabled={isLoading} className="gap-2">
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          {isLoading ? "開始中..." : "更新開始"}
        </Button>

        {/* エラー表示 */}
        {error && (
          <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
            <p className="text-sm text-destructive">{error}</p>
          </div>
        )}

        {/* 成功メッセージ */}
        {lastJobId && !error && (
          <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg flex items-center gap-3">
            <CheckCircle className="h-5 w-5 text-green-600" />
            <div>
              <p className="font-medium text-green-800 dark:text-green-200">
                更新処理を開始しました
              </p>
              <p className="text-sm text-green-600 dark:text-green-400 mt-1">
                Job ID: <span className="font-mono">{lastJobId.slice(0, 8)}</span>
                <br />
                バックグラウンドで処理が実行されます。
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
