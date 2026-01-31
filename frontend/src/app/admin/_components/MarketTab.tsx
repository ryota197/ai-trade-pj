"use client";

import { Play, Loader2, RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import type { FlowStatus } from "@/types/admin";
import { useMarketRefresh } from "../_hooks/useMarketRefresh";
import { useMarketFlowHistory } from "../_hooks/useMarketFlowHistory";

/** ステータスバッジの色とラベル */
const STATUS_CONFIG: Record<
  FlowStatus,
  { label: string; variant: "default" | "secondary" | "destructive" | "outline" }
> = {
  pending: { label: "待機中", variant: "secondary" },
  running: { label: "実行中", variant: "default" },
  completed: { label: "完了", variant: "outline" },
  failed: { label: "失敗", variant: "destructive" },
  cancelled: { label: "キャンセル", variant: "secondary" },
};

function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return "-";
  return new Date(dateStr).toLocaleString("ja-JP");
}

function formatDuration(start: string | null, end: string | null): string {
  if (!start || !end) return "-";
  const duration = new Date(end).getTime() - new Date(start).getTime();
  const seconds = Math.floor(duration / 1000);
  if (seconds < 60) return `${seconds}秒`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}分${remainingSeconds}秒`;
}

/**
 * マーケットタブ - マーケットデータ更新
 */
export function MarketTab() {
  const { isLoading, error, startRefresh } = useMarketRefresh();
  const {
    flows,
    refresh: refreshHistory,
    isLoading: isLoadingHistory,
  } = useMarketFlowHistory(5);
  const latestFlow = flows[0] ?? null;

  const handleStart = async () => {
    await startRefresh();
    refreshHistory();
  };

  const handleRefreshStatus = () => {
    refreshHistory();
  };

  return (
    <div className="space-y-6">
      {/* 更新パネル */}
      <Card>
        <CardHeader>
          <CardTitle>マーケットデータ更新</CardTitle>
          <CardDescription>
            VIX、S&P500、RSI、200日移動平均などのマーケット指標を更新します。
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

          {/* 最新フローの状態 */}
          {latestFlow && (
            <div className="p-4 bg-muted/50 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Badge variant={STATUS_CONFIG[latestFlow.status].variant}>
                    {STATUS_CONFIG[latestFlow.status].label}
                  </Badge>
                  <span className="text-sm">
                    {latestFlow.completed_jobs}/{latestFlow.total_jobs} ジョブ
                  </span>
                </div>
                <span className="text-xs text-muted-foreground">
                  {formatDateTime(latestFlow.started_at)}
                </span>
              </div>
              {latestFlow.jobs && latestFlow.jobs.length > 0 && (
                <div className="mt-3 text-sm">
                  {latestFlow.jobs.map((job) => (
                    <div
                      key={job.job_name}
                      className="flex items-center justify-between py-1"
                    >
                      <span className="text-muted-foreground">{job.job_name}</span>
                      <Badge
                        variant={
                          STATUS_CONFIG[job.status as FlowStatus]?.variant ||
                          "secondary"
                        }
                        className="text-xs"
                      >
                        {STATUS_CONFIG[job.status as FlowStatus]?.label ||
                          job.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 実行履歴 */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-lg">実行履歴</CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={refreshHistory}
            disabled={isLoadingHistory}
            className="gap-2"
          >
            <RefreshCw
              className={`h-4 w-4 ${isLoadingHistory ? "animate-spin" : ""}`}
            />
            更新
          </Button>
        </CardHeader>
        <CardContent>
          {flows.length === 0 && !isLoadingHistory && (
            <p className="text-sm text-muted-foreground">実行履歴がありません</p>
          )}

          {flows.length > 0 && (
            <div className="space-y-3">
              {flows.map((flow) => {
                const config = STATUS_CONFIG[flow.status];
                return (
                  <div
                    key={flow.flow_id}
                    className="flex items-center justify-between py-3 border-b last:border-0"
                  >
                    <div className="flex items-center gap-3">
                      <Badge variant={config.variant}>{config.label}</Badge>
                      <div>
                        <p className="text-sm">
                          {flow.completed_jobs}/{flow.total_jobs} ジョブ
                          {flow.completed_at && flow.started_at && (
                            <span className="text-muted-foreground ml-2">
                              ({formatDuration(flow.started_at, flow.completed_at)})
                            </span>
                          )}
                        </p>
                      </div>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {formatDateTime(flow.started_at)}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 注意事項 */}
      <div className="p-4 bg-muted/50 rounded-lg">
        <h3 className="font-medium mb-2">注意事項</h3>
        <ul className="text-sm text-muted-foreground space-y-1">
          <li>• マーケットデータは数秒で更新完了します</li>
          <li>• ダッシュボードのMarket Overviewに反映されます</li>
          <li>• Put/Call Ratioは現在固定値（0.85）を使用しています</li>
        </ul>
      </div>
    </div>
  );
}
