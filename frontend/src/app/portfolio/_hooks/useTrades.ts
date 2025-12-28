"use client";

import { useState, useEffect, useCallback } from "react";
import type {
  TradeListResponse,
  Trade,
  OpenPosition,
  OpenTradeRequest,
  CloseTradeRequest,
  TradeFilter,
} from "@/types/portfolio";
import type { ApiResponse } from "@/types/api";

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

  // filterのプリミティブ値を個別に抽出して依存配列に使用（オブジェクト参照の問題を回避）
  const { status, trade_type, symbol, limit, offset } = filter;

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (status) params.append("status", status);
      if (trade_type) params.append("trade_type", trade_type);
      if (symbol) params.append("symbol", symbol);
      if (limit) params.append("limit", limit.toString());
      if (offset) params.append("offset", offset.toString());

      const queryString = params.toString();
      const endpoint = queryString ? `/api/trades?${queryString}` : "/api/trades";

      const res = await fetch(endpoint, { cache: "no-store" });
      const response: ApiResponse<TradeListResponse> = await res.json();

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
  }, [status, trade_type, symbol, limit, offset]);

  const fetchPositions = useCallback(async () => {
    try {
      const res = await fetch("/api/trades?status=open", { cache: "no-store" });
      const response: ApiResponse<TradeListResponse> = await res.json();

      if (response.success && response.data) {
        // TradeListResponse から OpenPosition[] への変換
        const openPositions: OpenPosition[] = response.data.trades.map((trade) => ({
          id: trade.id,
          symbol: trade.symbol,
          trade_type: trade.trade_type,
          quantity: trade.quantity,
          entry_price: trade.entry_price,
          entry_date: trade.entry_date,
          stop_loss_price: trade.stop_loss_price,
          target_price: trade.target_price,
          position_value: trade.position_value,
          holding_days: trade.holding_days ?? 0,
          current_price: null, // 現在価格はバックエンドから別途取得が必要
          unrealized_pnl: trade.profit_loss, // オープントレードの場合は未実現損益
          unrealized_return_percent: trade.return_percent, // オープントレードの場合は未実現リターン
        }));
        setPositions(openPositions);
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

        const res = await fetch("/api/trades", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(request),
        });
        const response: ApiResponse<Trade> = await res.json();

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

        const res = await fetch(`/api/trades/${tradeId}/close`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(request),
        });
        const response: ApiResponse<Trade> = await res.json();

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

        const res = await fetch(`/api/trades/${tradeId}`, {
          method: "DELETE",
        });
        const response: ApiResponse<{ message: string }> = await res.json();

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
