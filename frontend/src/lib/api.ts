/**
 * API クライアント
 */

import type { ApiResponse, HealthResponse } from "@/types/api";
import type { MarketStatusResponse, MarketIndicatorsResponse } from "@/types/market";
import type { ScreenerResponse, ScreenerFilter, StockDetail } from "@/types/stock";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

/**
 * 共通fetchラッパー
 */
async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }

  return response.json();
}

/**
 * ヘルスチェックAPI
 */
export async function getHealth(): Promise<ApiResponse<HealthResponse>> {
  return fetchApi<ApiResponse<HealthResponse>>("/health");
}

/**
 * マーケット状態取得API
 */
export async function getMarketStatus(): Promise<ApiResponse<MarketStatusResponse>> {
  return fetchApi<ApiResponse<MarketStatusResponse>>("/market/status", {
    cache: "no-store",
  });
}

/**
 * マーケット指標取得API
 */
export async function getMarketIndicators(): Promise<ApiResponse<MarketIndicatorsResponse>> {
  return fetchApi<ApiResponse<MarketIndicatorsResponse>>("/market/indicators", {
    cache: "no-store",
  });
}

/**
 * CAN-SLIMスクリーニングAPI
 */
export async function screenStocks(
  filter: Partial<ScreenerFilter> = {}
): Promise<ApiResponse<ScreenerResponse>> {
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
  const endpoint = queryString ? `/screener/canslim?${queryString}` : "/screener/canslim";

  return fetchApi<ApiResponse<ScreenerResponse>>(endpoint, {
    cache: "no-store",
  });
}

/**
 * 銘柄詳細取得API
 */
export async function getStockDetail(symbol: string): Promise<ApiResponse<StockDetail>> {
  return fetchApi<ApiResponse<StockDetail>>(`/screener/stock/${symbol}`, {
    cache: "no-store",
  });
}
