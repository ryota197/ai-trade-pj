"use client";

import { useState, useEffect, useCallback } from "react";
import {
  getWatchlist,
  addToWatchlist,
  updateWatchlistItem,
  removeFromWatchlist,
} from "@/lib/api";
import type {
  WatchlistResponse,
  WatchlistItem,
  AddToWatchlistRequest,
  UpdateWatchlistRequest,
  WatchlistFilter,
} from "@/types/portfolio";

interface UseWatchlistResult {
  /** ウォッチリストデータ */
  data: WatchlistResponse | null;
  /** ローディング状態 */
  isLoading: boolean;
  /** エラーメッセージ */
  error: string | null;
  /** 追加中 */
  isAdding: boolean;
  /** 更新中 */
  isUpdating: boolean;
  /** 削除中 */
  isDeleting: boolean;
  /** ウォッチリストに追加 */
  add: (request: AddToWatchlistRequest) => Promise<WatchlistItem | null>;
  /** ウォッチリストを更新 */
  update: (
    symbol: string,
    request: UpdateWatchlistRequest
  ) => Promise<WatchlistItem | null>;
  /** ウォッチリストから削除 */
  remove: (symbol: string) => Promise<boolean>;
  /** 再取得 */
  refetch: () => Promise<void>;
}

/**
 * ウォッチリストカスタムフック
 */
export function useWatchlist(filter: WatchlistFilter = {}): UseWatchlistResult {
  const [data, setData] = useState<WatchlistResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await getWatchlist(filter);
      if (response.success && response.data) {
        setData(response.data);
      } else {
        setError("Failed to fetch watchlist");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const add = useCallback(
    async (request: AddToWatchlistRequest): Promise<WatchlistItem | null> => {
      try {
        setIsAdding(true);
        setError(null);
        const response = await addToWatchlist(request);
        if (response.success && response.data) {
          await fetchData(); // リストを再取得
          return response.data;
        }
        setError("Failed to add to watchlist");
        return null;
      } catch (e) {
        setError(e instanceof Error ? e.message : "Unknown error");
        return null;
      } finally {
        setIsAdding(false);
      }
    },
    [fetchData]
  );

  const update = useCallback(
    async (
      symbol: string,
      request: UpdateWatchlistRequest
    ): Promise<WatchlistItem | null> => {
      try {
        setIsUpdating(true);
        setError(null);
        const response = await updateWatchlistItem(symbol, request);
        if (response.success && response.data) {
          await fetchData(); // リストを再取得
          return response.data;
        }
        setError("Failed to update watchlist item");
        return null;
      } catch (e) {
        setError(e instanceof Error ? e.message : "Unknown error");
        return null;
      } finally {
        setIsUpdating(false);
      }
    },
    [fetchData]
  );

  const remove = useCallback(
    async (symbol: string): Promise<boolean> => {
      try {
        setIsDeleting(true);
        setError(null);
        const response = await removeFromWatchlist(symbol);
        if (response.success) {
          await fetchData(); // リストを再取得
          return true;
        }
        setError("Failed to remove from watchlist");
        return false;
      } catch (e) {
        setError(e instanceof Error ? e.message : "Unknown error");
        return false;
      } finally {
        setIsDeleting(false);
      }
    },
    [fetchData]
  );

  return {
    data,
    isLoading,
    error,
    isAdding,
    isUpdating,
    isDeleting,
    add,
    update,
    remove,
    refetch: fetchData,
  };
}
