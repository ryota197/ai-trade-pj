"use client";

import { useState, useEffect } from "react";
import type { FundamentalIndicators } from "@/types/stock";
import type { ApiResponse } from "@/types/api";

interface UseFundamentalsResult {
  data: FundamentalIndicators | null;
  isLoading: boolean;
  error: string | null;
}

/**
 * ファンダメンタル指標取得カスタムフック
 */
export function useFundamentals(symbol: string): UseFundamentalsResult {
  const [data, setData] = useState<FundamentalIndicators | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchFundamentals() {
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
    }

    if (symbol) {
      fetchFundamentals();
    }
  }, [symbol]);

  return { data, isLoading, error };
}
