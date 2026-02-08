"use client";

import { useState, useCallback } from "react";
import type { ApiResponse } from "@/types/api";

/** チャートデータのバー */
export interface ChartBar {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

/** チャートデータレスポンス */
export interface ChartDataResponse {
  symbol: string;
  period: string;
  data: ChartBar[];
}

/** 期間オプション */
export type ChartPeriod = "1mo" | "3mo" | "6mo" | "1y";

interface UseChartDataResult {
  /** チャートデータ */
  data: ChartDataResponse | null;
  /** ローディング状態 */
  isLoading: boolean;
  /** エラーメッセージ */
  error: string | null;
  /** データ取得 */
  fetchChartData: (symbol: string, period?: ChartPeriod) => Promise<void>;
  /** データクリア */
  clear: () => void;
}

/**
 * チャートデータ取得カスタムフック
 */
export function useChartData(): UseChartDataResult {
  const [data, setData] = useState<ChartDataResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchChartData = useCallback(
    async (symbol: string, period: ChartPeriod = "3mo") => {
      try {
        setIsLoading(true);
        setError(null);

        const res = await fetch(
          `/api/screener/stock/${symbol}/chart?period=${period}`,
          { cache: "no-store" }
        );
        const response: ApiResponse<ChartDataResponse> = await res.json();

        if (response.success && response.data) {
          setData(response.data);
        } else {
          setError(response.error || "Failed to fetch chart data");
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Unknown error");
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const clear = useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  return {
    data,
    isLoading,
    error,
    fetchChartData,
    clear,
  };
}
