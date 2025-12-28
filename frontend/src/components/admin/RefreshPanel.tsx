/**
 * RefreshPanel Component
 * スクリーニングデータ更新パネル
 */

"use client";

import { useState } from "react";
import { Play, Square, Clock, CheckCircle, XCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { ProgressBar } from "./ProgressBar";
import { ErrorList } from "./ErrorList";
import { useAdminRefresh } from "@/hooks/useAdminRefresh";

type SymbolSource = "sp500" | "nasdaq100";

const SOURCE_OPTIONS: { value: SymbolSource; label: string; description: string }[] = [
  { value: "sp500", label: "S&P 500", description: "S&P 500構成銘柄 (約500銘柄)" },
  { value: "nasdaq100", label: "NASDAQ 100", description: "NASDAQ 100構成銘柄 (約100銘柄)" },
];

function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}秒`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);
  return `${minutes}分${remainingSeconds}秒`;
}

function getStatusDisplay(status: string): { label: string; color: string; icon: React.ReactNode } {
  switch (status) {
    case "pending":
      return { label: "待機中", color: "text-yellow-600", icon: <Clock className="h-4 w-4" /> };
    case "running":
      return { label: "実行中", color: "text-blue-600", icon: <Loader2 className="h-4 w-4 animate-spin" /> };
    case "completed":
      return { label: "完了", color: "text-green-600", icon: <CheckCircle className="h-4 w-4" /> };
    case "failed":
      return { label: "失敗", color: "text-red-600", icon: <XCircle className="h-4 w-4" /> };
    case "cancelled":
      return { label: "キャンセル", color: "text-gray-600", icon: <Square className="h-4 w-4" /> };
    default:
      return { label: status, color: "text-muted-foreground", icon: null };
  }
}

export function RefreshPanel() {
  const [selectedSource, setSelectedSource] = useState<SymbolSource>("nasdaq100");
  const {
    jobStatus,
    isLoading,
    isRunning,
    error,
    startRefresh,
    cancelJob,
    clearStatus,
  } = useAdminRefresh();

  const handleStart = () => {
    startRefresh(selectedSource);
  };

  const statusDisplay = jobStatus ? getStatusDisplay(jobStatus.status) : null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>スクリーニングデータ更新</CardTitle>
        <CardDescription>
          指定されたシンボルリストの銘柄データを更新します。
          更新には時間がかかる場合があります。
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* ソース選択 */}
        {!isRunning && !jobStatus && (
          <div className="space-y-3">
            <label className="text-sm font-medium">更新対象</label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {SOURCE_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setSelectedSource(option.value)}
                  className={`p-4 rounded-lg border text-left transition-colors ${
                    selectedSource === option.value
                      ? "border-primary bg-primary/5"
                      : "border-border hover:border-muted-foreground/50"
                  }`}
                >
                  <div className="font-medium">{option.label}</div>
                  <div className="text-sm text-muted-foreground mt-1">
                    {option.description}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* アクションボタン */}
        <div className="flex gap-3">
          {!isRunning && !jobStatus && (
            <Button onClick={handleStart} disabled={isLoading} className="gap-2">
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Play className="h-4 w-4" />
              )}
              更新開始
            </Button>
          )}

          {isRunning && (
            <Button
              variant="destructive"
              onClick={cancelJob}
              disabled={isLoading}
              className="gap-2"
            >
              <Square className="h-4 w-4" />
              キャンセル
            </Button>
          )}

          {jobStatus && !isRunning && (
            <Button variant="outline" onClick={clearStatus} className="gap-2">
              新しい更新を開始
            </Button>
          )}
        </div>

        {/* エラー表示 */}
        {error && (
          <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
            <p className="text-sm text-destructive">{error}</p>
          </div>
        )}

        {/* ジョブステータス */}
        {jobStatus && (
          <div className="space-y-4">
            {/* ステータスバッジ */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className={statusDisplay?.color}>{statusDisplay?.icon}</span>
                <span className={`font-medium ${statusDisplay?.color}`}>
                  {statusDisplay?.label}
                </span>
              </div>
              <div className="text-sm text-muted-foreground">
                Job ID: <span className="font-mono">{jobStatus.job_id.slice(0, 8)}</span>
              </div>
            </div>

            {/* プログレスバー */}
            <ProgressBar
              percentage={jobStatus.progress.percentage}
              processed={jobStatus.progress.processed}
              total={jobStatus.progress.total}
              succeeded={jobStatus.progress.succeeded}
              failed={jobStatus.progress.failed}
            />

            {/* タイミング情報 */}
            <div className="flex gap-6 text-sm text-muted-foreground">
              <div>
                <span>経過時間: </span>
                <span className="font-medium text-foreground">
                  {formatDuration(jobStatus.timing.elapsed_seconds)}
                </span>
              </div>
              {jobStatus.timing.estimated_remaining_seconds !== null && isRunning && (
                <div>
                  <span>残り時間: </span>
                  <span className="font-medium text-foreground">
                    約 {formatDuration(jobStatus.timing.estimated_remaining_seconds)}
                  </span>
                </div>
              )}
            </div>

            {/* エラー一覧 */}
            <ErrorList errors={jobStatus.errors} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
