"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import type {
  ScreenerResponse,
  ScreenerFilter,
  StockSummary,
  SortKey,
  SortOrder,
} from "@/types/stock";
import { DEFAULT_SCREENER_FILTER } from "@/types/stock";
import type { ApiResponse } from "@/types/api";

interface UseScreenerResult {
  /** スクリーニング結果 */
  data: ScreenerResponse | null;
  /** ソート済み銘柄リスト */
  sortedStocks: StockSummary[];
  /** ローディング状態 */
  isLoading: boolean;
  /** エラーメッセージ */
  error: string | null;
  /** 現在のフィルター */
  filter: ScreenerFilter;
  /** フィルター更新 */
  setFilter: (filter: Partial<ScreenerFilter>) => void;
  /** フィルターリセット */
  resetFilter: () => void;
  /** ソートキー */
  sortKey: SortKey;
  /** ソート順 */
  sortOrder: SortOrder;
  /** ソート設定 */
  setSort: (key: SortKey) => void;
  /** 再取得 */
  refetch: () => Promise<void>;
}

/**
 * スクリーナーカスタムフック
 */
export function useScreener(): UseScreenerResult {
  const [data, setData] = useState<ScreenerResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilterState] = useState<ScreenerFilter>(DEFAULT_SCREENER_FILTER);
  const [sortKey, setSortKey] = useState<SortKey>("canslim_score");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (filter.min_rs_rating !== undefined) {
        params.append("min_rs_rating", filter.min_rs_rating.toString());
      }
      if (filter.min_eps_growth_quarterly !== undefined) {
        params.append("min_eps_growth_quarterly", filter.min_eps_growth_quarterly.toString());
      }
      if (filter.min_eps_growth_annual !== undefined) {
        params.append("min_eps_growth_annual", filter.min_eps_growth_annual.toString());
      }
      if (filter.max_distance_from_52w_high !== undefined) {
        params.append("max_distance_from_52w_high", filter.max_distance_from_52w_high.toString());
      }
      if (filter.min_volume_ratio !== undefined) {
        params.append("min_volume_ratio", filter.min_volume_ratio.toString());
      }
      if (filter.min_canslim_score !== undefined) {
        params.append("min_canslim_score", filter.min_canslim_score.toString());
      }

      const queryString = params.toString();
      const endpoint = queryString ? `/api/screener/canslim?${queryString}` : "/api/screener/canslim";

      const res = await fetch(endpoint, { cache: "no-store" });
      const response: ApiResponse<ScreenerResponse> = await res.json();

      if (response.success && response.data) {
        setData(response.data);
      } else {
        setError("Failed to fetch screener data");
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

  const setFilter = useCallback((newFilter: Partial<ScreenerFilter>) => {
    setFilterState((prev) => ({ ...prev, ...newFilter }));
  }, []);

  const resetFilter = useCallback(() => {
    setFilterState(DEFAULT_SCREENER_FILTER);
  }, []);

  const setSort = useCallback(
    (key: SortKey) => {
      if (key === sortKey) {
        setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
      } else {
        setSortKey(key);
        setSortOrder("desc");
      }
    },
    [sortKey]
  );

  const sortedStocks = useMemo(() => {
    if (!data?.stocks) return [];

    const sorted = [...data.stocks].sort((a, b) => {
      let aValue: number | string;
      let bValue: number | string;

      switch (sortKey) {
        case "symbol":
          aValue = a.symbol;
          bValue = b.symbol;
          break;
        case "name":
          aValue = a.name;
          bValue = b.name;
          break;
        case "price":
          aValue = a.price;
          bValue = b.price;
          break;
        case "change_percent":
          aValue = a.change_percent;
          bValue = b.change_percent;
          break;
        case "rs_rating":
          aValue = a.rs_rating;
          bValue = b.rs_rating;
          break;
        case "canslim_score":
          aValue = a.canslim_score;
          bValue = b.canslim_score;
          break;
        default:
          return 0;
      }

      if (typeof aValue === "string" && typeof bValue === "string") {
        return sortOrder === "asc"
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }

      if (typeof aValue === "number" && typeof bValue === "number") {
        return sortOrder === "asc" ? aValue - bValue : bValue - aValue;
      }

      return 0;
    });

    return sorted;
  }, [data?.stocks, sortKey, sortOrder]);

  return {
    data,
    sortedStocks,
    isLoading,
    error,
    filter,
    setFilter,
    resetFilter,
    sortKey,
    sortOrder,
    setSort,
    refetch: fetchData,
  };
}
