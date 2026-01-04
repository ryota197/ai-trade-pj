"use client";

import {
  Clock,
  Loader2,
  CheckCircle,
  XCircle,
  SkipForward,
} from "lucide-react";
import type { JobExecution, JobStatus } from "@/types/admin";
import { formatDuration } from "../_lib/format";

interface JobStepListProps {
  jobs: JobExecution[];
}

/** ジョブ名の日本語表示 */
const JOB_NAMES: Record<string, string> = {
  collect_stock_data: "データ収集",
  calculate_rs_rating: "RS Rating 計算",
  calculate_canslim: "CAN-SLIM スコア計算",
};

/** ステータスアイコン */
function JobStatusIcon({ status }: { status: JobStatus }) {
  switch (status) {
    case "completed":
      return <CheckCircle className="h-4 w-4 text-green-600" />;
    case "running":
      return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />;
    case "failed":
      return <XCircle className="h-4 w-4 text-red-600" />;
    case "skipped":
      return <SkipForward className="h-4 w-4 text-orange-500" />;
    case "pending":
    default:
      return <Clock className="h-4 w-4 text-muted-foreground" />;
  }
}

/**
 * ジョブステップリスト
 *
 * 各ジョブのステータスと実行時間を表示する。
 */
export function JobStepList({ jobs }: JobStepListProps) {
  if (jobs.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      {jobs.map((job) => (
        <div
          key={job.job_name}
          className="flex items-center gap-3 py-2 px-3 rounded-lg bg-muted/30"
        >
          <JobStatusIcon status={job.status} />
          <div className="flex-1 min-w-0">
            <span className="text-sm font-medium">
              {JOB_NAMES[job.job_name] || job.job_name}
            </span>
            {job.error_message && (
              <p className="text-xs text-destructive mt-0.5 truncate">
                {job.error_message}
              </p>
            )}
          </div>
          {job.status === "running" && (
            <span className="text-xs text-muted-foreground">実行中...</span>
          )}
          {job.status === "completed" && job.started_at && job.completed_at && (
            <span className="text-xs text-muted-foreground">
              {formatDuration(job.started_at, job.completed_at, { short: true })}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}
