"use client";

import { useState, useCallback } from "react";

type SymbolSource = "sp500" | "nasdaq100";

interface StartRefreshResponse {
  job_id: string;
  status: string;
  total_symbols: number;
  started_at: string | null;
}

interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error?: { code: string; message: string };
}

interface UseAdminRefreshReturn {
  /** ローディング中かどうか */
  isLoading: boolean;
  /** エラーメッセージ */
  error: string | null;
  /** 最後に開始したジョブID */
  lastJobId: string | null;
  /** 更新開始 */
  startRefresh: (source: SymbolSource) => Promise<void>;
}

/**
 * スクリーニングデータ更新フック（シンプル版）
 *
 * ジョブを開始するだけ。進捗は表示しない。
 */
export function useAdminRefresh(): UseAdminRefreshReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastJobId, setLastJobId] = useState<string | null>(null);

  const startRefresh = useCallback(async (source: SymbolSource) => {
    setIsLoading(true);
    setError(null);
    setLastJobId(null);

    try {
      const res = await fetch("/api/admin/screener/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error?.message || "更新開始に失敗しました");
      }

      const data: ApiResponse<StartRefreshResponse> = await res.json();

      if (!data.success || !data.data) {
        throw new Error(data.error?.message || "更新開始に失敗しました");
      }

      setLastJobId(data.data.job_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新開始に失敗しました");
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    isLoading,
    error,
    lastJobId,
    startRefresh,
  };
}
