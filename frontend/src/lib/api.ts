/**
 * API クライアント
 */

import type { ApiResponse, HealthResponse } from "@/types/api";
import type { MarketStatusResponse, MarketIndicatorsResponse } from "@/types/market";

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
