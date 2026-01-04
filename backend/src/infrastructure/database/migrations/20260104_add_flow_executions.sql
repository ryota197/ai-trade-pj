-- Migration: Add flow_executions and update job_executions
-- Date: 2026-01-04
-- Description: ジョブ進捗追跡のための親子テーブル構造を導入
-- Reference: docs/poc/plan/job-progress-tracking.md

-- =====================================================
-- Step 1: 既存の job_executions テーブルを削除
-- =====================================================
DROP TABLE IF EXISTS job_executions;

-- =====================================================
-- Step 2: flow_executions テーブルを作成（親）
-- =====================================================
CREATE TABLE flow_executions (
    flow_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    flow_name VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',

    -- 進捗サマリ
    total_jobs INT NOT NULL DEFAULT 3,
    completed_jobs INT NOT NULL DEFAULT 0,
    current_job VARCHAR(50),

    -- タイミング
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 制約
    CONSTRAINT valid_flow_status CHECK (
        status IN ('pending', 'running', 'completed', 'failed', 'cancelled')
    )
);

COMMENT ON TABLE flow_executions IS 'フロー実行（親）- RefreshScreenerFlow等の実行管理';
COMMENT ON COLUMN flow_executions.flow_id IS 'フローID（UUID）';
COMMENT ON COLUMN flow_executions.flow_name IS 'フロー名: refresh_screener など';
COMMENT ON COLUMN flow_executions.status IS '状態: pending/running/completed/failed/cancelled';
COMMENT ON COLUMN flow_executions.total_jobs IS '総ジョブ数';
COMMENT ON COLUMN flow_executions.completed_jobs IS '完了ジョブ数';
COMMENT ON COLUMN flow_executions.current_job IS '現在実行中のジョブ名';
COMMENT ON COLUMN flow_executions.started_at IS '開始日時';
COMMENT ON COLUMN flow_executions.completed_at IS '完了日時';
COMMENT ON COLUMN flow_executions.created_at IS '作成日時';

CREATE INDEX idx_flow_executions_status ON flow_executions(status, created_at DESC);

-- =====================================================
-- Step 3: job_executions テーブルを作成（子）
-- =====================================================
CREATE TABLE job_executions (
    flow_id UUID NOT NULL REFERENCES flow_executions(flow_id) ON DELETE CASCADE,
    job_name VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',

    -- タイミング
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- 結果
    result JSONB,
    error_message TEXT,

    -- 制約
    PRIMARY KEY (flow_id, job_name),
    CONSTRAINT valid_job_status CHECK (
        status IN ('pending', 'running', 'completed', 'failed', 'skipped')
    )
);

COMMENT ON TABLE job_executions IS 'ジョブ実行（子）- 各ジョブの実行状態';
COMMENT ON COLUMN job_executions.flow_id IS '親フローID（FK）';
COMMENT ON COLUMN job_executions.job_name IS 'ジョブ名: collect_stock_data/calculate_rs_rating/calculate_canslim';
COMMENT ON COLUMN job_executions.status IS '状態: pending/running/completed/failed/skipped';
COMMENT ON COLUMN job_executions.started_at IS '開始日時';
COMMENT ON COLUMN job_executions.completed_at IS '完了日時';
COMMENT ON COLUMN job_executions.result IS '実行結果（JSON）';
COMMENT ON COLUMN job_executions.error_message IS 'エラー時のメッセージ';
