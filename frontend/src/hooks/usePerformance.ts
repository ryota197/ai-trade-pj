"use client";

import { useState, useEffect, useCallback } from "react";
import { getPerformance, getDetailedPerformance } from "@/lib/api";
import type {
  Performance,
  DetailedPerformanceResponse,
} from "@/types/portfolio";

interface UsePerformanceResult {
  /** パフォーマンスデータ */
  data: Performance | null;
  /** 詳細パフォーマンスデータ */
  detailedData: DetailedPerformanceResponse | null;
  /** ローディング状態 */
  isLoading: boolean;
  /** エラーメッセージ */
  error: string | null;
  /** 再取得 */
  refetch: () => Promise<void>;
  /** 詳細を取得 */
  fetchDetailed: () => Promise<void>;
}

interface UsePerformanceOptions {
  /** 開始日 */
  startDate?: string;
  /** 終了日 */
  endDate?: string;
  /** 詳細も取得するか */
  includeDetailed?: boolean;
}

/**
 * パフォーマンスカスタムフック
 */
export function usePerformance(
  options: UsePerformanceOptions = {}
): UsePerformanceResult {
  const { startDate, endDate, includeDetailed = false } = options;

  const [data, setData] = useState<Performance | null>(null);
  const [detailedData, setDetailedData] =
    useState<DetailedPerformanceResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await getPerformance(startDate, endDate);
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

  const fetchDetailed = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await getDetailedPerformance(startDate, endDate);
      if (response.success && response.data) {
        setDetailedData(response.data);
        setData(response.data.summary);
      } else {
        setError("Failed to fetch detailed performance");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  }, [startDate, endDate]);

  useEffect(() => {
    if (includeDetailed) {
      fetchDetailed();
    } else {
      fetchData();
    }
  }, [fetchData, fetchDetailed, includeDetailed]);

  return {
    data,
    detailedData,
    isLoading,
    error,
    refetch: fetchData,
    fetchDetailed,
  };
}
