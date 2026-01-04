"use client";

import { Badge } from "@/components/ui/badge";
import type { FlowStatusResponse, FlowStatus } from "@/types/admin";
import { formatDateTime, formatDuration } from "../_lib/format";
import { JobStepList } from "./JobStepList";

interface FlowProgressProps {
  status: FlowStatusResponse;
}

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

/**
 * フロー進捗表示
 *
 * プログレスバー、ステータス、ジョブリストを表示する。
 */
export function FlowProgress({ status }: FlowProgressProps) {
  const progress =
    status.total_jobs > 0
      ? (status.completed_jobs / status.total_jobs) * 100
      : 0;
  const config = STATUS_CONFIG[status.status];

  return (
    <div className="space-y-4 p-4 border rounded-lg bg-card">
      {/* ヘッダー */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Badge variant={config.variant}>{config.label}</Badge>
          {status.status === "running" && (
            <span className="text-sm text-muted-foreground">
              {status.current_job && `${status.current_job} を処理中`}
            </span>
          )}
        </div>
        <span className="text-sm text-muted-foreground">
          {status.completed_jobs} / {status.total_jobs} ジョブ
        </span>
      </div>

      {/* プログレスバー */}
      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-300 ${
            status.status === "failed"
              ? "bg-destructive"
              : status.status === "completed"
                ? "bg-green-600"
                : "bg-primary"
          }`}
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* タイミング情報 */}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>開始: {formatDateTime(status.started_at)}</span>
        {status.completed_at && (
          <span>
            所要時間: {formatDuration(status.started_at, status.completed_at)}
          </span>
        )}
      </div>

      {/* ジョブリスト */}
      <JobStepList jobs={status.jobs} />
    </div>
  );
}
