"use client";

import { Play, Loader2, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { useAdminRefresh } from "../_hooks/useAdminRefresh";
import { useFlowHistory } from "../_hooks/useFlowHistory";
import { FlowProgress } from "./FlowProgress";

/**
 * スクリーニングデータ更新パネル
 */
export function RefreshPanel() {
  const { isLoading, error, startRefresh } = useAdminRefresh();
  const { flows, refresh: refreshHistory, isLoading: isLoadingHistory } = useFlowHistory(1);
  const latestFlow = flows[0] ?? null;

  const handleStart = async () => {
    await startRefresh("sp500");
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
