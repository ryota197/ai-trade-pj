"use client";

import { RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import type { FlowStatus } from "@/types/admin";
import { formatDateTime, formatDuration } from "../_lib/format";
import { useFlowHistory } from "../_hooks/useFlowHistory";

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
 * フロー履歴表示
 *
 * 過去のフロー実行履歴を一覧表示する。
 */
export function FlowHistory() {
  const { flows, isLoading, error, refresh } = useFlowHistory(5);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg">実行履歴</CardTitle>
        <Button
          variant="ghost"
          size="sm"
          onClick={refresh}
          disabled={isLoading}
          className="gap-2"
        >
          <RefreshCw
            className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`}
          />
          更新
        </Button>
      </CardHeader>
      <CardContent>
        {error && (
          <p className="text-sm text-destructive">{error}</p>
        )}

        {!error && flows.length === 0 && !isLoading && (
          <p className="text-sm text-muted-foreground">
            実行履歴がありません
          </p>
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
  );
}
