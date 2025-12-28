/**
 * Admin Screener Refresh Hook
 * スクリーニングデータ更新管理用カスタムフック
 */

import { useState, useCallback, useEffect, useRef } from "react";

interface RefreshJobProgress {
  total: number;
  processed: number;
  succeeded: number;
  failed: number;
  percentage: number;
}

interface RefreshJobTiming {
  started_at: string | null;
  elapsed_seconds: number;
  estimated_remaining_seconds: number | null;
}

interface RefreshJobError {
  symbol: string;
  error: string;
}

interface RefreshJobStatus {
  job_id: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  progress: RefreshJobProgress;
  timing: RefreshJobTiming;
  errors: RefreshJobError[];
}

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

type SymbolSource = "sp500" | "nasdaq100" | "custom";

interface UseAdminRefreshReturn {
  /** 現在のジョブステータス */
  jobStatus: RefreshJobStatus | null;
  /** ローディング中かどうか */
  isLoading: boolean;
  /** 更新処理が進行中かどうか */
  isRunning: boolean;
  /** エラーメッセージ */
  error: string | null;
  /** 更新開始 */
  startRefresh: (source: SymbolSource, customSymbols?: string[]) => Promise<void>;
  /** ジョブキャンセル */
  cancelJob: () => Promise<void>;
  /** ステータスをクリア */
  clearStatus: () => void;
}

const POLLING_INTERVAL = 2000; // 2秒

export function useAdminRefresh(): UseAdminRefreshReturn {
  const [jobStatus, setJobStatus] = useState<RefreshJobStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const jobIdRef = useRef<string | null>(null);

  const isRunning =
    jobStatus?.status === "pending" || jobStatus?.status === "running";

  // ポーリング停止
  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  // ジョブステータス取得
  const fetchJobStatus = useCallback(async (jobId: string) => {
    try {
      const res = await fetch(`/api/admin/screener/refresh/${jobId}`, {
        cache: "no-store",
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error?.message || "ステータス取得に失敗しました");
      }

      const data: ApiResponse<RefreshJobStatus> = await res.json();

      if (!data.success || !data.data) {
        throw new Error(data.error?.message || "ステータス取得に失敗しました");
      }

      setJobStatus(data.data);

      // 完了・失敗・キャンセルの場合はポーリング停止
      if (["completed", "failed", "cancelled"].includes(data.data.status)) {
        stopPolling();
      }
    } catch (err) {
      console.error("Failed to fetch job status:", err);
      // ポーリング中のエラーは無視（ネットワーク一時エラーなど）
    }
  }, [stopPolling]);

  // ポーリング開始
  const startPolling = useCallback(
    (jobId: string) => {
      stopPolling();
      jobIdRef.current = jobId;

      // 即座に1回取得
      fetchJobStatus(jobId);

      // 定期的にポーリング
      pollingRef.current = setInterval(() => {
        fetchJobStatus(jobId);
      }, POLLING_INTERVAL);
    },
    [fetchJobStatus, stopPolling]
  );

  // 更新開始
  const startRefresh = useCallback(
    async (source: SymbolSource, customSymbols?: string[]) => {
      setIsLoading(true);
      setError(null);

      try {
        // symbolsの準備
        let symbols: string[] = [];
        if (source === "custom" && customSymbols) {
          symbols = customSymbols;
        }

        const body = {
          symbols,
          source: source === "custom" ? undefined : source,
        };

        const res = await fetch("/api/admin/screener/refresh", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });

        if (!res.ok) {
          const errorData = await res.json();
          throw new Error(errorData.error?.message || "更新開始に失敗しました");
        }

        const data: ApiResponse<StartRefreshResponse> = await res.json();

        if (!data.success || !data.data) {
          throw new Error(data.error?.message || "更新開始に失敗しました");
        }

        // ポーリング開始
        startPolling(data.data.job_id);
      } catch (err) {
        setError(err instanceof Error ? err.message : "更新開始に失敗しました");
      } finally {
        setIsLoading(false);
      }
    },
    [startPolling]
  );

  // ジョブキャンセル
  const cancelJob = useCallback(async () => {
    if (!jobIdRef.current) return;

    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch(`/api/admin/screener/refresh/${jobIdRef.current}`, {
        method: "DELETE",
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error?.message || "キャンセルに失敗しました");
      }

      // ステータス更新
      await fetchJobStatus(jobIdRef.current);
    } catch (err) {
      setError(err instanceof Error ? err.message : "キャンセルに失敗しました");
    } finally {
      setIsLoading(false);
    }
  }, [fetchJobStatus]);

  // ステータスクリア
  const clearStatus = useCallback(() => {
    stopPolling();
    setJobStatus(null);
    setError(null);
    jobIdRef.current = null;
  }, [stopPolling]);

  // クリーンアップ
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  return {
    jobStatus,
    isLoading,
    isRunning,
    error,
    startRefresh,
    cancelJob,
    clearStatus,
  };
}
