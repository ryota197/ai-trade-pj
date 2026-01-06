"use client";

import { useState, useCallback } from "react";
import type { RefreshResponse } from "@/types/admin";
import type { ApiResponse } from "@/types/api";

interface UseAdminRefreshReturn {
  /** ローディング中かどうか */
  isLoading: boolean;
  /** エラーメッセージ */
  error: string | null;
  /** 最後に開始したフローID */
  lastFlowId: string | null;
  /** 更新開始 */
  startRefresh: () => Promise<string | null>;
}

/**
 * スクリーニングデータ更新フック
 *
 * フローを開始し、flow_id を返す。
 */
export function useAdminRefresh(): UseAdminRefreshReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastFlowId, setLastFlowId] = useState<string | null>(null);

  const startRefresh = useCallback(async (): Promise<string | null> => {
    setIsLoading(true);
    setError(null);
    setLastFlowId(null);

    try {
      const res = await fetch("/api/admin/screener/refresh", {
        method: "POST",
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error?.message || "更新開始に失敗しました");
      }

      const data: ApiResponse<RefreshResponse> = await res.json();

      if (!data.success || !data.data) {
        throw new Error(data.error || "更新開始に失敗しました");
      }

      setLastFlowId(data.data.flow_id);
      return data.data.flow_id;
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新開始に失敗しました");
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    isLoading,
    error,
    lastFlowId,
    startRefresh,
  };
}
