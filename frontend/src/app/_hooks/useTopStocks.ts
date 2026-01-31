"use client";

import { useState, useEffect, useCallback } from "react";
import type { StockSummary } from "@/types/stock";
import type { ApiResponse } from "@/types/api";

interface ScreenerResponse {
  stocks: StockSummary[];
  total: number;
  screened_at: string;
}

interface UseTopStocksResult {
  /** Top銘柄リスト（CAN-SLIMスコア降順） */
  stocks: StockSummary[];
  /** ローディング状態 */
  isLoading: boolean;
  /** エラーメッセージ */
  error: string | null;
  /** 再取得 */
  refetch: () => Promise<void>;
}

/**
 * Top CAN-SLIM銘柄取得フック
 *
 * @param limit 取得件数（デフォルト: 5）
 */
export function useTopStocks(limit: number = 5): UseTopStocksResult {
  const [stocks, setStocks] = useState<StockSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const res = await fetch("/api/screener/canslim", { cache: "no-store" });
      const response: ApiResponse<ScreenerResponse> = await res.json();

      if (response.success && response.data) {
        // CAN-SLIMスコア降順でソートしてlimit件取得
        const sorted = [...response.data.stocks]
          .sort((a, b) => b.canslim_score - a.canslim_score)
          .slice(0, limit);
        setStocks(sorted);
      } else {
        setError("スクリーニングデータの取得に失敗しました");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    stocks,
    isLoading,
    error,
    refetch: fetchData,
  };
}
