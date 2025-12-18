/**
 * API レスポンス型定義
 */

/** 共通APIレスポンス */
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: string;
}

/** ヘルスチェックレスポンス */
export interface HealthResponse {
  status: string;
  database: string;
}
