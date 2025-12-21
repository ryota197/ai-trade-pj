"use client";

import { useState, useEffect, useCallback } from "react";
import {
  getTrades,
  getOpenPositions,
  openTrade,
  closeTrade,
  cancelTrade,
} from "@/lib/api";
import type {
  TradeListResponse,
  Trade,
  OpenPosition,
  OpenTradeRequest,
  CloseTradeRequest,
  TradeFilter,
} from "@/types/portfolio";

interface UseTradesResult {
  /** トレードデータ */
  data: TradeListResponse | null;
  /** オープンポジション */
  positions: OpenPosition[];
  /** ローディング状態 */
  isLoading: boolean;
  /** エラーメッセージ */
  error: string | null;
  /** 作成中 */
  isCreating: boolean;
  /** 決済中 */
  isClosing: boolean;
  /** キャンセル中 */
  isCancelling: boolean;
  /** 新規ポジションを開く */
  open: (request: OpenTradeRequest) => Promise<Trade | null>;
  /** ポジションを決済 */
  close: (tradeId: number, request: CloseTradeRequest) => Promise<Trade | null>;
  /** トレードをキャンセル */
  cancel: (tradeId: number) => Promise<boolean>;
  /** 再取得 */
  refetch: () => Promise<void>;
  /** ポジション再取得 */
  refetchPositions: () => Promise<void>;
}

/**
 * トレードカスタムフック
 */
export function useTrades(filter: TradeFilter = {}): UseTradesResult {
  const [data, setData] = useState<TradeListResponse | null>(null);
  const [positions, setPositions] = useState<OpenPosition[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isClosing, setIsClosing] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await getTrades(filter);
      if (response.success && response.data) {
        setData(response.data);
      } else {
        setError("Failed to fetch trades");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  }, [filter]);

  const fetchPositions = useCallback(async () => {
    try {
      const response = await getOpenPositions();
      if (response.success && response.data) {
        setPositions(response.data);
      }
    } catch (e) {
      console.error("Failed to fetch positions:", e);
    }
  }, []);

  useEffect(() => {
    fetchData();
    fetchPositions();
  }, [fetchData, fetchPositions]);

  const open = useCallback(
    async (request: OpenTradeRequest): Promise<Trade | null> => {
      try {
        setIsCreating(true);
        setError(null);
        const response = await openTrade(request);
        if (response.success && response.data) {
          await fetchData();
          await fetchPositions();
          return response.data;
        }
        setError("Failed to open trade");
        return null;
      } catch (e) {
        setError(e instanceof Error ? e.message : "Unknown error");
        return null;
      } finally {
        setIsCreating(false);
      }
    },
    [fetchData, fetchPositions]
  );

  const close = useCallback(
    async (
      tradeId: number,
      request: CloseTradeRequest
    ): Promise<Trade | null> => {
      try {
        setIsClosing(true);
        setError(null);
        const response = await closeTrade(tradeId, request);
        if (response.success && response.data) {
          await fetchData();
          await fetchPositions();
          return response.data;
        }
        setError("Failed to close trade");
        return null;
      } catch (e) {
        setError(e instanceof Error ? e.message : "Unknown error");
        return null;
      } finally {
        setIsClosing(false);
      }
    },
    [fetchData, fetchPositions]
  );

  const cancel = useCallback(
    async (tradeId: number): Promise<boolean> => {
      try {
        setIsCancelling(true);
        setError(null);
        const response = await cancelTrade(tradeId);
        if (response.success) {
          await fetchData();
          await fetchPositions();
          return true;
        }
        setError("Failed to cancel trade");
        return false;
      } catch (e) {
        setError(e instanceof Error ? e.message : "Unknown error");
        return false;
      } finally {
        setIsCancelling(false);
      }
    },
    [fetchData, fetchPositions]
  );

  return {
    data,
    positions,
    isLoading,
    error,
    isCreating,
    isClosing,
    isCancelling,
    open,
    close,
    cancel,
    refetch: fetchData,
    refetchPositions: fetchPositions,
  };
}
