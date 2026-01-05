/**
 * 管理画面 型定義
 */

// ジョブステータス
export type JobStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "skipped";

// フローステータス
export type FlowStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

// ジョブ実行情報
export interface JobExecution {
  job_name: string;
  status: JobStatus;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
}

// フローステータスレスポンス
export interface FlowStatusResponse {
  flow_id: string;
  flow_name: string;
  status: FlowStatus;
  total_jobs: number;
  completed_jobs: number;
  current_job: string | null;
  started_at: string | null;
  completed_at: string | null;
  jobs: JobExecution[];
}

// 更新開始レスポンス
export interface RefreshResponse {
  flow_id: string;
  status: string;
  message: string;
}

// シンボルソース（PoC実装ではS&P500のみ対応）
export type SymbolSource = "sp500";

// 更新開始リクエスト
export interface RefreshRequest {
  symbols?: string[];
  source: SymbolSource;
}
