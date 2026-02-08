"use client";

import { useState, useCallback } from "react";
import type { FundamentalIndicators } from "@/types/stock";
import type { ApiResponse } from "@/types/api";

interface UseFundamentalsResult {
  /** ファンダメンタル指標データ */
  data: FundamentalIndicators | null;
  /** ローディング状態 */
  isLoading: boolean;
  /** エラーメッセージ */
  error: string | null;
  /** データ取得 */
  fetchFundamentals: (symbol: string) => Promise<void>;
  /** データクリア */
  clear: () => void;
}

/**
 * ファンダメンタル指標取得カスタムフック
 */
export function useFundamentals(): UseFundamentalsResult {
  const [data, setData] = useState<FundamentalIndicators | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFundamentals = useCallback(async (symbol: string) => {
    try {
      setIsLoading(true);
      setError(null);

      const res = await fetch(`/api/screener/stock/${symbol}/fundamentals`, {
        cache: "no-store",
      });
      const response: ApiResponse<FundamentalIndicators> = await res.json();

      if (response.success && response.data) {
        setData(response.data);
      } else {
        setError(response.error || "Failed to fetch fundamentals");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clear = useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  return {
    data,
    isLoading,
    error,
    fetchFundamentals,
    clear,
  };
}
