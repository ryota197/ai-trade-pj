/**
 * API クライアント
 *
 * Next.js Route Handlers (BFF) 経由でバックエンドAPIを呼び出す。
 * すべてのリクエストは /api/* を通じてサーバーサイドでプロキシされる。
 */

import type { ApiResponse, HealthResponse } from "@/types/api";
import type { MarketStatusResponse, MarketIndicatorsResponse } from "@/types/market";
import type {
  WatchlistResponse,
  WatchlistItem,
  AddToWatchlistRequest,
  UpdateWatchlistRequest,
  TradeListResponse,
  Trade,
  OpenTradeRequest,
  CloseTradeRequest,
  OpenPosition,
  Performance,
  DetailedPerformanceResponse,
  TradeFilter,
  WatchlistFilter,
} from "@/types/portfolio";
import type {
  ScreenerResponse,
  ScreenerFilter,
  StockDetail,
  PriceHistoryResponse,
  FinancialsResponse,
} from "@/types/stock";

/**
 * API Base URL
 * Next.js Route Handlers を使用（同一オリジン）
 */
const API_BASE_URL = "/api";

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
 * Note: BFF経由ではなく直接バックエンドを呼び出す（開発用）
 */
export async function getHealth(): Promise<ApiResponse<HealthResponse>> {
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
  const response = await fetch(`${backendUrl}/api/health`);
  return response.json();
}

// ============================================================
// マーケット API
// ============================================================

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

// ============================================================
// スクリーナー API
// ============================================================

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

// ============================================================
// データ API
// ============================================================

/**
 * 株価履歴取得API
 */
export async function getPriceHistory(
  symbol: string,
  period: string = "1y",
  interval: string = "1d"
): Promise<ApiResponse<PriceHistoryResponse>> {
  const params = new URLSearchParams({ period, interval });
  return fetchApi<ApiResponse<PriceHistoryResponse>>(
    `/data/history/${symbol}?${params.toString()}`,
    { cache: "no-store" }
  );
}

/**
 * 財務指標取得API
 */
export async function getFinancials(
  symbol: string
): Promise<ApiResponse<FinancialsResponse>> {
  return fetchApi<ApiResponse<FinancialsResponse>>(`/data/financials/${symbol}`, {
    cache: "no-store",
  });
}

/**
 * 株価クォート取得API
 */
export async function getQuote(symbol: string): Promise<ApiResponse<{
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
}>> {
  return fetchApi(`/data/quote/${symbol}`, { cache: "no-store" });
}

// ============================================================
// ウォッチリスト API
// ============================================================

/**
 * ウォッチリスト一覧取得API
 */
export async function getWatchlist(
  filter: WatchlistFilter = {}
): Promise<ApiResponse<WatchlistResponse>> {
  const params = new URLSearchParams();
  if (filter.status) params.append("status", filter.status);
  if (filter.limit) params.append("limit", filter.limit.toString());
  if (filter.offset) params.append("offset", filter.offset.toString());

  const queryString = params.toString();
  const endpoint = queryString ? `/watchlist?${queryString}` : "/watchlist";

  return fetchApi<ApiResponse<WatchlistResponse>>(endpoint, { cache: "no-store" });
}

/**
 * ウォッチリスト追加API
 */
export async function addToWatchlist(
  data: AddToWatchlistRequest
): Promise<ApiResponse<WatchlistItem>> {
  return fetchApi<ApiResponse<WatchlistItem>>("/watchlist", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * ウォッチリスト更新API
 */
export async function updateWatchlistItem(
  symbol: string,
  data: UpdateWatchlistRequest
): Promise<ApiResponse<WatchlistItem>> {
  return fetchApi<ApiResponse<WatchlistItem>>(`/watchlist/${symbol}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

/**
 * ウォッチリスト削除API
 */
export async function removeFromWatchlist(
  symbol: string
): Promise<ApiResponse<{ message: string }>> {
  return fetchApi<ApiResponse<{ message: string }>>(
    `/watchlist/${symbol}`,
    { method: "DELETE" }
  );
}

// ============================================================
// トレード API
// ============================================================

/**
 * トレード一覧取得API
 */
export async function getTrades(
  filter: TradeFilter = {}
): Promise<ApiResponse<TradeListResponse>> {
  const params = new URLSearchParams();
  if (filter.status) params.append("status", filter.status);
  if (filter.trade_type) params.append("trade_type", filter.trade_type);
  if (filter.symbol) params.append("symbol", filter.symbol);
  if (filter.limit) params.append("limit", filter.limit.toString());
  if (filter.offset) params.append("offset", filter.offset.toString());

  const queryString = params.toString();
  const endpoint = queryString ? `/trades?${queryString}` : "/trades";

  return fetchApi<ApiResponse<TradeListResponse>>(endpoint, { cache: "no-store" });
}

/**
 * オープンポジション取得API
 * Note: このエンドポイントはBFF未実装のため、trades APIから取得してフィルタリング
 */
export async function getOpenPositions(): Promise<ApiResponse<OpenPosition[]>> {
  const result = await getTrades({ status: "open" });
  // TradeListResponse から OpenPosition[] への変換が必要な場合はここで行う
  return result as unknown as ApiResponse<OpenPosition[]>;
}

/**
 * 新規トレード作成API
 */
export async function openTrade(
  data: OpenTradeRequest
): Promise<ApiResponse<Trade>> {
  return fetchApi<ApiResponse<Trade>>("/trades", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * トレード決済API
 */
export async function closeTrade(
  tradeId: number,
  data: CloseTradeRequest
): Promise<ApiResponse<Trade>> {
  return fetchApi<ApiResponse<Trade>>(`/trades/${tradeId}/close`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * トレードキャンセルAPI
 */
export async function cancelTrade(
  tradeId: number
): Promise<ApiResponse<{ message: string }>> {
  return fetchApi<ApiResponse<{ message: string }>>(
    `/trades/${tradeId}`,
    { method: "DELETE" }
  );
}

// ============================================================
// パフォーマンス API
// ============================================================

/**
 * パフォーマンス取得API
 */
export async function getPerformance(
  startDate?: string,
  endDate?: string
): Promise<ApiResponse<Performance>> {
  const params = new URLSearchParams();
  if (startDate) params.append("start_date", startDate);
  if (endDate) params.append("end_date", endDate);

  const queryString = params.toString();
  const endpoint = queryString ? `/performance?${queryString}` : "/performance";

  return fetchApi<ApiResponse<Performance>>(endpoint, { cache: "no-store" });
}

/**
 * 詳細パフォーマンス取得API
 * Note: このエンドポイントはBFF未実装のため、通常のperformance APIを使用
 */
export async function getDetailedPerformance(
  startDate?: string,
  endDate?: string
): Promise<ApiResponse<DetailedPerformanceResponse>> {
  // 詳細パフォーマンスのBFFルートを追加するか、通常のパフォーマンスで代用
  return getPerformance(startDate, endDate) as unknown as Promise<ApiResponse<DetailedPerformanceResponse>>;
}
