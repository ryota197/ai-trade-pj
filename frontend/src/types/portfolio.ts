/**
 * ポートフォリオ関連 型定義
 */

// ============================================================
// ウォッチリスト
// ============================================================

/** ウォッチリストアイテム */
export interface WatchlistItem {
  id: number;
  symbol: string;
  added_at: string;
  target_entry_price: number | null;
  stop_loss_price: number | null;
  target_price: number | null;
  notes: string | null;
  status: WatchlistStatus;
  triggered_at: string | null;
  risk_reward_ratio: number | null;
  potential_loss_percent: number | null;
  potential_gain_percent: number | null;
}

/** ウォッチリストステータス */
export type WatchlistStatus = "watching" | "triggered" | "expired" | "removed";

/** ウォッチリスト追加リクエスト */
export interface AddToWatchlistRequest {
  symbol: string;
  target_entry_price?: number;
  stop_loss_price?: number;
  target_price?: number;
  notes?: string;
}

/** ウォッチリスト更新リクエスト */
export interface UpdateWatchlistRequest {
  target_entry_price?: number;
  stop_loss_price?: number;
  target_price?: number;
  notes?: string;
}

/** ウォッチリストレスポンス */
export interface WatchlistResponse {
  items: WatchlistItem[];
  total_count: number;
  watching_count: number;
}

// ============================================================
// トレード
// ============================================================

/** トレード */
export interface Trade {
  id: number;
  symbol: string;
  trade_type: TradeType;
  quantity: number;
  entry_price: number;
  entry_date: string;
  exit_price: number | null;
  exit_date: string | null;
  stop_loss_price: number | null;
  target_price: number | null;
  status: TradeStatus;
  notes: string | null;
  created_at: string;
  position_value: number;
  profit_loss: number | null;
  return_percent: number | null;
  holding_days: number | null;
  is_winner: boolean | null;
}

/** トレードタイプ */
export type TradeType = "buy" | "sell";

/** トレードステータス */
export type TradeStatus = "open" | "closed" | "cancelled";

/** 新規トレードリクエスト */
export interface OpenTradeRequest {
  symbol: string;
  trade_type: TradeType;
  quantity: number;
  entry_price: number;
  stop_loss_price?: number;
  target_price?: number;
  notes?: string;
}

/** トレード決済リクエスト */
export interface CloseTradeRequest {
  exit_price: number;
}

/** トレード一覧レスポンス */
export interface TradeListResponse {
  trades: Trade[];
  total_count: number;
  open_count: number;
  closed_count: number;
}

/** オープンポジション */
export interface OpenPosition {
  id: number;
  symbol: string;
  trade_type: TradeType;
  quantity: number;
  entry_price: number;
  entry_date: string;
  stop_loss_price: number | null;
  target_price: number | null;
  position_value: number;
  holding_days: number;
  current_price: number | null;
  unrealized_pnl: number | null;
  unrealized_return_percent: number | null;
}

// ============================================================
// パフォーマンス
// ============================================================

/** パフォーマンス指標 */
export interface Performance {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  total_profit_loss: number;
  total_return_percent: number;
  average_return_percent: number;
  win_rate: number;
  average_win: number;
  average_loss: number;
  profit_factor: number | null;
  expectancy: number;
  risk_reward_ratio: number | null;
  max_drawdown_percent: number;
  max_consecutive_wins: number;
  max_consecutive_losses: number;
  average_holding_days: number;
  is_profitable: boolean;
  has_sufficient_trades: boolean;
  calculated_at: string;
}

/** 月別リターン */
export interface MonthlyReturn {
  month: string;
  return_percent: number;
  trade_count: number;
}

/** シンボル別統計 */
export interface SymbolStats {
  symbol: string;
  total_trades: number;
  winning_trades: number;
  total_profit_loss: number;
  win_rate: number;
}

/** 詳細パフォーマンスレスポンス */
export interface DetailedPerformanceResponse {
  summary: Performance;
  monthly_returns: MonthlyReturn[];
  symbol_stats: SymbolStats[];
}

// ============================================================
// フィルター
// ============================================================

/** トレードフィルター */
export interface TradeFilter {
  status?: TradeStatus;
  trade_type?: TradeType;
  symbol?: string;
  limit?: number;
  offset?: number;
}

/** ウォッチリストフィルター */
export interface WatchlistFilter {
  status?: WatchlistStatus;
  limit?: number;
  offset?: number;
}
