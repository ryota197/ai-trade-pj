"use client";

import { useState, useCallback, useEffect } from "react";
import type { FlowStatusResponse } from "@/types/admin";
import type { ApiResponse } from "@/types/api";

interface UseMarketFlowHistoryReturn {
  /** フロー履歴 */
  flows: FlowStatusResponse[];
  /** ローディング中かどうか */
  isLoading: boolean;
  /** エラーメッセージ */
  error: string | null;
  /** 履歴を再取得 */
  refresh: () => Promise<void>;
}

/**
 * マーケットフロー履歴取得フック
 *
 * 最新のマーケットデータ更新フロー実行履歴を取得する。
 *
 * @param limit 取得件数（デフォルト: 10）
 */
export function useMarketFlowHistory(
  limit: number = 10
): UseMarketFlowHistoryReturn {
  const [flows, setFlows] = useState<FlowStatusResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch(
        `/api/admin/market/refresh/latest?limit=${limit}`,
        { cache: "no-store" }
      );

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error?.message || "履歴取得に失敗しました");
      }

      const data: ApiResponse<FlowStatusResponse[]> = await res.json();

      if (!data.success || !data.data) {
        throw new Error(data.error || "履歴取得に失敗しました");
      }

      setFlows(data.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "履歴取得に失敗しました");
    } finally {
      setIsLoading(false);
    }
  }, [limit]);

  // 初期ロード
  useEffect(() => {
    refresh();
  }, [refresh]);

  return {
    flows,
    isLoading,
    error,
    refresh,
  };
}
