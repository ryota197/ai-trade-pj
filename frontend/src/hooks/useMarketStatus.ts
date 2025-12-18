"use client";

import { useState, useEffect, useCallback } from "react";
import { getMarketStatus } from "@/lib/api";
import type { MarketStatusResponse } from "@/types/market";

interface UseMarketStatusResult {
  data: MarketStatusResponse | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * マーケット状態取得カスタムフック
 *
 * @param autoRefresh - 自動更新間隔（ミリ秒）。0の場合は自動更新しない
 */
export function useMarketStatus(autoRefresh = 0): UseMarketStatusResult {
  const [data, setData] = useState<MarketStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await getMarketStatus();
      if (response.success) {
        setData(response.data);
      } else {
        setError("Failed to fetch market status");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();

    if (autoRefresh > 0) {
      const interval = setInterval(fetchData, autoRefresh);
      return () => clearInterval(interval);
    }
  }, [fetchData, autoRefresh]);

  return { data, isLoading, error, refetch: fetchData };
}
