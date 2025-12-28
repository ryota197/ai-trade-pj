"use client";

import { useState, useEffect, useCallback } from "react";
import type { Performance } from "@/types/portfolio";
import type { ApiResponse } from "@/types/api";

interface UsePerformanceResult {
  /** パフォーマンスデータ */
  data: Performance | null;
  /** ローディング状態 */
  isLoading: boolean;
  /** エラーメッセージ */
  error: string | null;
  /** 再取得 */
  refetch: () => Promise<void>;
}

interface UsePerformanceOptions {
  /** 開始日 */
  startDate?: string;
  /** 終了日 */
  endDate?: string;
}

/**
 * パフォーマンスカスタムフック
 */
export function usePerformance(
  options: UsePerformanceOptions = {}
): UsePerformanceResult {
  const { startDate, endDate } = options;

  const [data, setData] = useState<Performance | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (startDate) params.append("start_date", startDate);
      if (endDate) params.append("end_date", endDate);

      const queryString = params.toString();
      const endpoint = queryString ? `/api/performance?${queryString}` : "/api/performance";

      const res = await fetch(endpoint, { cache: "no-store" });
      const response: ApiResponse<Performance> = await res.json();

      if (response.success && response.data) {
        setData(response.data);
      } else {
        setError("Failed to fetch performance");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  }, [startDate, endDate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    isLoading,
    error,
    refetch: fetchData,
  };
}
