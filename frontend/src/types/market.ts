/**
 * マーケット関連 型定義
 */

/** シグナル種別 */
export type SignalType = "bullish" | "neutral" | "bearish";

/** マーケット状態 */
export type MarketCondition = "risk_on" | "risk_off" | "neutral";

/** マーケット指標 */
export interface MarketIndicators {
  vix: number;
  vix_signal: SignalType;
  sp500_price: number;
  sp500_rsi: number;
  sp500_rsi_signal: SignalType;
  sp500_ma200: number;
  sp500_above_ma200: boolean;
  put_call_ratio: number;
  put_call_signal: SignalType;
  retrieved_at: string;
}

/** マーケット状態レスポンス */
export interface MarketStatusResponse {
  condition: MarketCondition;
  condition_label: string;
  confidence: number;
  score: number;
  recommendation: string;
  indicators: MarketIndicators;
  analyzed_at: string;
}

/** マーケット指標レスポンス */
export interface MarketIndicatorsResponse extends MarketIndicators {}
