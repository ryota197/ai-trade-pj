"use client";

import { useState, useEffect, useCallback } from "react";
import type { PriceBar, FinancialsResponse, CANSLIMScore, StockDetail } from "@/types/stock";
import type { ApiResponse } from "@/types/api";

/** 株価クォートデータ */
export interface QuoteData {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  market_cap: number | null;
  pe_ratio: number | null;
  week_52_high: number;
  week_52_low: number;
  timestamp: string;
}

/** 株価履歴レスポンス */
interface PriceHistoryResponse {
  symbol: string;
  period: string;
  interval: string;
  data: PriceBar[];
}

/** useStockDataの戻り値 */
export interface UseStockDataResult {
  quote: QuoteData | null;
  priceHistory: PriceBar[];
  financials: FinancialsResponse | null;
  canslimScore: CANSLIMScore | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * 銘柄データ取得フック
 *
 * 株価クォート、価格履歴、財務データを並列取得する
 */
export function useStockData(
  symbol: string,
  period: string = "1y"
): UseStockDataResult {
  const [quote, setQuote] = useState<QuoteData | null>(null);
  const [priceHistory, setPriceHistory] = useState<PriceBar[]>([]);
  const [financials, setFinancials] = useState<FinancialsResponse | null>(null);
  const [canslimScore, setCanslimScore] = useState<CANSLIMScore | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!symbol) return;

    setIsLoading(true);
    setError(null);

    try {
      // 並列でデータ取得
      const [quoteRes, historyRes, financialsRes, stockDetailRes] = await Promise.all([
        fetch(`/api/data/quote/${symbol}`, { cache: "no-store" })
          .then((r) => r.json() as Promise<ApiResponse<QuoteData>>),
        fetch(`/api/data/history/${symbol}?period=${period}&interval=1d`, { cache: "no-store" })
          .then((r) => r.json() as Promise<ApiResponse<PriceHistoryResponse>>),
        fetch(`/api/data/financials/${symbol}`, { cache: "no-store" })
          .then((r) => r.json() as Promise<ApiResponse<FinancialsResponse>>)
          .catch(() => null), // 財務データは取得失敗しても続行
        fetch(`/api/screener/stock/${symbol}`, { cache: "no-store" })
          .then((r) => r.json() as Promise<ApiResponse<StockDetail>>)
          .catch(() => null), // CAN-SLIMスコアは取得失敗しても続行
      ]);

      if (quoteRes.success && quoteRes.data) {
        setQuote(quoteRes.data);
      } else {
        throw new Error("Failed to fetch quote data");
      }

      if (historyRes.success && historyRes.data) {
        setPriceHistory(historyRes.data.data);
      }

      if (financialsRes?.success && financialsRes.data) {
        setFinancials(financialsRes.data);
      }

      if (stockDetailRes?.success && stockDetailRes.data?.canslim_score) {
        setCanslimScore(stockDetailRes.data.canslim_score);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch stock data");
    } finally {
      setIsLoading(false);
    }
  }, [symbol, period]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    quote,
    priceHistory,
    financials,
    canslimScore,
    isLoading,
    error,
    refetch: fetchData,
  };
}
