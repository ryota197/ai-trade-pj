/**
 * 株式・スクリーナー関連 型定義
 */

/** CAN-SLIM基準項目 */
export interface CANSLIMCriteria {
  name: string;
  score: number;
  grade: string;
  value: number | null;
  threshold: number;
  description: string;
}

/** CAN-SLIMスコア */
export interface CANSLIMScore {
  total_score: number;
  overall_grade: string;
  passing_count: number;
  c_score: CANSLIMCriteria;
  a_score: CANSLIMCriteria;
  n_score: CANSLIMCriteria;
  s_score: CANSLIMCriteria;
  l_score: CANSLIMCriteria;
  i_score: CANSLIMCriteria;
}

/** 銘柄サマリー（一覧表示用） */
export interface StockSummary {
  symbol: string;
  name: string;
  price: number;
  change_percent: number;
  rs_rating: number;
  canslim_score: number;
  volume_ratio: number;
  distance_from_52w_high: number;
}

/** スクリーニングフィルター */
export interface ScreenerFilter {
  min_rs_rating: number;
  min_eps_growth_quarterly: number;
  min_eps_growth_annual: number;
  max_distance_from_52w_high: number;
  min_volume_ratio: number;
  min_canslim_score: number;
}

/** スクリーニング結果レスポンス */
export interface ScreenerResponse {
  total_count: number;
  stocks: StockSummary[];
  filter_applied: ScreenerFilter;
  screened_at: string;
}

/** 銘柄詳細 */
export interface StockDetail {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  avg_volume: number;
  market_cap: number | null;
  pe_ratio: number | null;
  week_52_high: number;
  week_52_low: number;
  eps_growth_quarterly: number | null;
  eps_growth_annual: number | null;
  rs_rating: number;
  institutional_ownership: number | null;
  canslim_score: CANSLIMScore | null;
  updated_at: string;
}

/** フィルターのデフォルト値 */
export const DEFAULT_SCREENER_FILTER: ScreenerFilter = {
  min_rs_rating: 80,
  min_eps_growth_quarterly: 25.0,
  min_eps_growth_annual: 25.0,
  max_distance_from_52w_high: 15.0,
  min_volume_ratio: 1.5,
  min_canslim_score: 70,
};

/** 株価履歴バー */
export interface PriceBar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

/** 株価履歴レスポンス */
export interface PriceHistoryResponse {
  symbol: string;
  period: string;
  interval: string;
  data: PriceBar[];
}

/** 財務指標レスポンス */
export interface FinancialsResponse {
  symbol: string;
  eps_ttm: number | null;
  eps_growth_quarterly: number | null;
  eps_growth_annual: number | null;
  revenue_growth: number | null;
  profit_margin: number | null;
  roe: number | null;
  debt_to_equity: number | null;
  institutional_ownership: number | null;
  retrieved_at: string;
}

/** ソートキー */
export type SortKey =
  | "symbol"
  | "name"
  | "price"
  | "change_percent"
  | "rs_rating"
  | "canslim_score";

/** ソート順 */
export type SortOrder = "asc" | "desc";
