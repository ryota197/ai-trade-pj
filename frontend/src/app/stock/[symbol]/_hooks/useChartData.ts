"use client";

import { useState, useEffect, useCallback } from "react";
import type { ApiResponse } from "@/types/api";

export interface ChartBar {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ChartDataResponse {
  symbol: string;
  period: string;
  data: ChartBar[];
}

export type ChartPeriod = "1mo" | "3mo" | "6mo" | "1y";

interface UseChartDataResult {
  data: ChartDataResponse | null;
  isLoading: boolean;
  error: string | null;
  period: ChartPeriod;
  setPeriod: (period: ChartPeriod) => void;
}

/**
 * チャートデータ取得カスタムフック
 */
export function useChartData(symbol: string): UseChartDataResult {
  const [data, setData] = useState<ChartDataResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<ChartPeriod>("3mo");

  useEffect(() => {
    async function fetchChartData() {
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
    }

    if (symbol) {
      fetchChartData();
    }
  }, [symbol, period]);

  return { data, isLoading, error, period, setPeriod };
}
