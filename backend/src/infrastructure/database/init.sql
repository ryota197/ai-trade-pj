-- init.sql
-- Docker起動時に自動実行される初期化スクリプト

-- 拡張機能
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- stocks: 銘柄マスター
-- =====================================================
CREATE TABLE stocks (
    symbol VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100),
    industry VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE stocks IS '銘柄マスター（基本情報のみ）';
COMMENT ON COLUMN stocks.symbol IS 'ティッカーシンボル（例: AAPL）';
COMMENT ON COLUMN stocks.name IS '企業名';
COMMENT ON COLUMN stocks.industry IS '業種';
COMMENT ON COLUMN stocks.created_at IS '作成日時';
COMMENT ON COLUMN stocks.updated_at IS '更新日時';

-- =====================================================
-- stock_prices: 価格スナップショット（日次）
-- =====================================================
CREATE TABLE stock_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL REFERENCES stocks(symbol) ON DELETE CASCADE,
    price DECIMAL(10,2),
    change_percent DECIMAL(10,2),
    volume BIGINT,
    avg_volume_50d BIGINT,
    market_cap BIGINT,
    week_52_high DECIMAL(10,2),
    week_52_low DECIMAL(10,2),
    recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_stock_price_per_day
        UNIQUE (symbol, (recorded_at::date))
);

COMMENT ON TABLE stock_prices IS '価格スナップショット（日次蓄積）';
COMMENT ON COLUMN stock_prices.symbol IS 'ティッカーシンボル';
COMMENT ON COLUMN stock_prices.price IS '現在株価';
COMMENT ON COLUMN stock_prices.change_percent IS '前日比変動率（%）';
COMMENT ON COLUMN stock_prices.volume IS '出来高';
COMMENT ON COLUMN stock_prices.avg_volume_50d IS '50日平均出来高';
COMMENT ON COLUMN stock_prices.market_cap IS '時価総額（USD）';
COMMENT ON COLUMN stock_prices.week_52_high IS '52週高値';
COMMENT ON COLUMN stock_prices.week_52_low IS '52週安値';
COMMENT ON COLUMN stock_prices.recorded_at IS '記録日時';

CREATE INDEX idx_stock_prices_symbol_date
    ON stock_prices(symbol, recorded_at DESC);

-- =====================================================
-- stock_metrics: 計算指標（CAN-SLIM関連）
-- =====================================================
CREATE TABLE stock_metrics (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL REFERENCES stocks(symbol) ON DELETE CASCADE,

    -- ファンダメンタル（Job 1 で取得）
    eps_growth_quarterly DECIMAL(10,2),
    eps_growth_annual DECIMAL(10,2),
    institutional_ownership DECIMAL(10,2),

    -- RS関連（Job 0, 1, 2 で段階的に設定）
    relative_strength DECIMAL(10,4),  -- Job 1: S&P500比の生値
    rs_rating INTEGER,                 -- Job 2: パーセンタイル (1-99)

    -- CAN-SLIMスコア（Job 3 で設定）
    canslim_score INTEGER,             -- 0-100

    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_rs_rating
        CHECK (rs_rating IS NULL OR (rs_rating >= 1 AND rs_rating <= 99)),
    CONSTRAINT valid_canslim_score
        CHECK (canslim_score IS NULL OR (canslim_score >= 0 AND canslim_score <= 100)),
    CONSTRAINT unique_stock_metrics_per_day
        UNIQUE (symbol, (calculated_at::date))
);

COMMENT ON TABLE stock_metrics IS '計算指標（CAN-SLIM関連）';
COMMENT ON COLUMN stock_metrics.symbol IS 'ティッカーシンボル';
COMMENT ON COLUMN stock_metrics.eps_growth_quarterly IS 'C: 四半期EPS成長率（%）';
COMMENT ON COLUMN stock_metrics.eps_growth_annual IS 'A: 年間EPS成長率（%）';
COMMENT ON COLUMN stock_metrics.institutional_ownership IS 'I: 機関投資家保有率（%）';
COMMENT ON COLUMN stock_metrics.relative_strength IS 'S&P500比の相対強度（生値）- Job 1で保存';
COMMENT ON COLUMN stock_metrics.rs_rating IS 'L: RS Rating（1-99パーセンタイル）- Job 2で更新';
COMMENT ON COLUMN stock_metrics.canslim_score IS 'CAN-SLIMスコア（0-100）- Job 3で更新';
COMMENT ON COLUMN stock_metrics.calculated_at IS '計算日時';

CREATE INDEX idx_stock_metrics_symbol_date
    ON stock_metrics(symbol, calculated_at DESC);
CREATE INDEX idx_stock_metrics_rs_rating
    ON stock_metrics(rs_rating DESC) WHERE rs_rating IS NOT NULL;
CREATE INDEX idx_stock_metrics_canslim
    ON stock_metrics(canslim_score DESC) WHERE canslim_score IS NOT NULL;

-- =====================================================
-- market_benchmarks: 市場ベンチマーク（Job 0 で更新）
-- =====================================================
CREATE TABLE market_benchmarks (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,  -- "^GSPC" (S&P500), "^NDX" (NASDAQ100)
    performance_1y DECIMAL(10,4),
    performance_9m DECIMAL(10,4),
    performance_6m DECIMAL(10,4),
    performance_3m DECIMAL(10,4),
    performance_1m DECIMAL(10,4),
    weighted_performance DECIMAL(10,4),  -- IBD式加重平均（40/20/20/20）
    recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_benchmark_per_day
        UNIQUE (symbol, (recorded_at::date))
);

COMMENT ON TABLE market_benchmarks IS '市場ベンチマーク（Job 0 で1日1回更新）';
COMMENT ON COLUMN market_benchmarks.symbol IS '指数シンボル（^GSPC: S&P500, ^NDX: NASDAQ100）';
COMMENT ON COLUMN market_benchmarks.performance_1y IS '1年パフォーマンス（%）';
COMMENT ON COLUMN market_benchmarks.performance_9m IS '9ヶ月パフォーマンス（%）';
COMMENT ON COLUMN market_benchmarks.performance_6m IS '6ヶ月パフォーマンス（%）';
COMMENT ON COLUMN market_benchmarks.performance_3m IS '3ヶ月パフォーマンス（%）';
COMMENT ON COLUMN market_benchmarks.performance_1m IS '1ヶ月パフォーマンス（%）';
COMMENT ON COLUMN market_benchmarks.weighted_performance IS 'IBD式加重パフォーマンス（3M×40% + 6M×20% + 9M×20% + 12M×20%）';
COMMENT ON COLUMN market_benchmarks.recorded_at IS '記録日時';

CREATE INDEX idx_market_benchmarks_symbol_date
    ON market_benchmarks(symbol, recorded_at DESC);

-- =====================================================
-- market_snapshots: マーケット状態の履歴
-- =====================================================
CREATE TABLE market_snapshots (
    id SERIAL PRIMARY KEY,
    recorded_at TIMESTAMP NOT NULL,

    -- VIX関連
    vix DECIMAL(10,2) NOT NULL,
    vix_signal VARCHAR(20) NOT NULL,

    -- S&P500指標
    sp500_price DECIMAL(12,2) NOT NULL,
    sp500_rsi DECIMAL(5,2) NOT NULL,
    sp500_rsi_signal VARCHAR(20) NOT NULL,
    sp500_ma200 DECIMAL(12,2) NOT NULL,
    sp500_above_ma200 BOOLEAN NOT NULL,

    -- Put/Call Ratio
    put_call_ratio DECIMAL(6,4) NOT NULL,
    put_call_signal VARCHAR(20) NOT NULL,

    -- 判定結果
    market_condition VARCHAR(20) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    score INTEGER NOT NULL,
    recommendation VARCHAR(500) NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_market_condition CHECK (market_condition IN ('risk_on', 'risk_off', 'neutral')),
    CONSTRAINT valid_vix_signal CHECK (vix_signal IN ('bullish', 'neutral', 'bearish')),
    CONSTRAINT valid_rsi_signal CHECK (sp500_rsi_signal IN ('bullish', 'neutral', 'bearish')),
    CONSTRAINT valid_pc_signal CHECK (put_call_signal IN ('bullish', 'neutral', 'bearish'))
);

COMMENT ON TABLE market_snapshots IS 'マーケット状態の履歴スナップショット';
COMMENT ON COLUMN market_snapshots.recorded_at IS 'スナップショット取得日時';
COMMENT ON COLUMN market_snapshots.vix IS 'VIX指数（恐怖指数）';
COMMENT ON COLUMN market_snapshots.vix_signal IS 'VIXシグナル: bullish/neutral/bearish';
COMMENT ON COLUMN market_snapshots.sp500_price IS 'S&P500現在価格';
COMMENT ON COLUMN market_snapshots.sp500_rsi IS 'S&P500のRSI（14日）';
COMMENT ON COLUMN market_snapshots.sp500_rsi_signal IS 'RSIシグナル: bullish/neutral/bearish';
COMMENT ON COLUMN market_snapshots.sp500_ma200 IS 'S&P500の200日移動平均';
COMMENT ON COLUMN market_snapshots.sp500_above_ma200 IS 'S&P500が200日移動平均線より上か';
COMMENT ON COLUMN market_snapshots.put_call_ratio IS 'Put/Call Ratio';
COMMENT ON COLUMN market_snapshots.put_call_signal IS 'Put/Call Ratioシグナル: bullish/neutral/bearish';
COMMENT ON COLUMN market_snapshots.market_condition IS '判定結果: risk_on/risk_off/neutral';
COMMENT ON COLUMN market_snapshots.confidence IS '判定の確信度（0.0-1.0）';
COMMENT ON COLUMN market_snapshots.score IS '総合スコア（-5〜+5）';
COMMENT ON COLUMN market_snapshots.recommendation IS '推奨アクション';

CREATE INDEX idx_market_snapshots_recorded_at ON market_snapshots(recorded_at DESC);

-- =====================================================
-- watchlist: ウォッチリスト
-- =====================================================
CREATE TABLE watchlist (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,

    -- 目標価格
    target_entry_price DECIMAL(10,2),
    stop_loss_price DECIMAL(10,2),
    target_profit_price DECIMAL(10,2),

    -- パターン・メモ
    pattern_detected VARCHAR(50),
    notes TEXT,

    -- アラート
    alert_enabled BOOLEAN NOT NULL DEFAULT true,

    -- メタデータ
    added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE watchlist IS '監視銘柄リスト';
COMMENT ON COLUMN watchlist.symbol IS 'ティッカーシンボル';
COMMENT ON COLUMN watchlist.target_entry_price IS 'エントリー目標価格';
COMMENT ON COLUMN watchlist.stop_loss_price IS 'ストップロス価格';
COMMENT ON COLUMN watchlist.target_profit_price IS '利確目標価格';
COMMENT ON COLUMN watchlist.pattern_detected IS '検出されたパターン';
COMMENT ON COLUMN watchlist.notes IS 'メモ（エントリー理由など）';
COMMENT ON COLUMN watchlist.alert_enabled IS 'アラート有効';
COMMENT ON COLUMN watchlist.added_at IS '追加日時';
COMMENT ON COLUMN watchlist.updated_at IS '更新日時';

CREATE INDEX idx_watchlist_symbol ON watchlist(symbol);

-- =====================================================
-- paper_trades: ペーパートレード記録
-- =====================================================
CREATE TABLE paper_trades (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,

    -- トレード情報
    trade_type VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,

    -- エントリー
    entry_price DECIMAL(10,2) NOT NULL,

    -- エグジット
    exit_price DECIMAL(10,2),

    -- ステータス
    status VARCHAR(20) NOT NULL DEFAULT 'open',

    -- 戦略・メモ
    strategy VARCHAR(50),
    notes TEXT,

    -- タイミング
    traded_at TIMESTAMP NOT NULL,
    closed_at TIMESTAMP,

    -- メタデータ
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_trade_type CHECK (trade_type IN ('buy', 'sell')),
    CONSTRAINT valid_trade_status CHECK (status IN ('open', 'closed', 'cancelled')),
    CONSTRAINT positive_quantity CHECK (quantity > 0),
    CONSTRAINT positive_entry_price CHECK (entry_price > 0)
);

COMMENT ON TABLE paper_trades IS 'ペーパートレード（仮想売買）記録';
COMMENT ON COLUMN paper_trades.symbol IS 'ティッカーシンボル';
COMMENT ON COLUMN paper_trades.trade_type IS '売買種別: buy/sell';
COMMENT ON COLUMN paper_trades.quantity IS '数量（株数）';
COMMENT ON COLUMN paper_trades.entry_price IS 'エントリー価格';
COMMENT ON COLUMN paper_trades.exit_price IS '決済価格';
COMMENT ON COLUMN paper_trades.status IS 'ステータス: open/closed/cancelled';
COMMENT ON COLUMN paper_trades.strategy IS '戦略（breakout/pullback等）';
COMMENT ON COLUMN paper_trades.notes IS 'メモ';
COMMENT ON COLUMN paper_trades.traded_at IS '取引日時';
COMMENT ON COLUMN paper_trades.closed_at IS '決済日時';
COMMENT ON COLUMN paper_trades.created_at IS '作成日時';

CREATE INDEX idx_paper_trades_symbol ON paper_trades(symbol);
CREATE INDEX idx_paper_trades_status ON paper_trades(status);
CREATE INDEX idx_paper_trades_traded_at ON paper_trades(traded_at DESC);

-- =====================================================
-- price_cache: 株価データキャッシュ
-- =====================================================
CREATE TABLE price_cache (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,

    -- OHLCV
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    adj_close DECIMAL(10,2),
    volume BIGINT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_symbol_date UNIQUE (symbol, date)
);

COMMENT ON TABLE price_cache IS '株価データキャッシュ（API呼び出し削減用、2年保持）';
COMMENT ON COLUMN price_cache.symbol IS 'ティッカーシンボル';
COMMENT ON COLUMN price_cache.date IS '取引日';
COMMENT ON COLUMN price_cache.open IS '始値';
COMMENT ON COLUMN price_cache.high IS '高値';
COMMENT ON COLUMN price_cache.low IS '安値';
COMMENT ON COLUMN price_cache.close IS '終値';
COMMENT ON COLUMN price_cache.adj_close IS '調整後終値（分割・配当調整済み）';
COMMENT ON COLUMN price_cache.volume IS '出来高';

CREATE INDEX idx_price_cache_symbol_date ON price_cache(symbol, date DESC);

-- =====================================================
-- job_executions: ジョブ実行履歴
-- =====================================================
CREATE TABLE job_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP NOT NULL,
    duration_seconds INTEGER NOT NULL,
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_job_status CHECK (status IN ('completed', 'failed'))
);

COMMENT ON TABLE job_executions IS 'ジョブ実行履歴（完了時に1回INSERT）';
COMMENT ON COLUMN job_executions.id IS 'ジョブID（UUID）';
COMMENT ON COLUMN job_executions.job_type IS 'ジョブ種別（collect_benchmarks, collect_stock_data等）';
COMMENT ON COLUMN job_executions.status IS '結果: completed/failed';
COMMENT ON COLUMN job_executions.started_at IS '開始日時';
COMMENT ON COLUMN job_executions.completed_at IS '完了日時';
COMMENT ON COLUMN job_executions.duration_seconds IS '実行時間（秒）';
COMMENT ON COLUMN job_executions.result IS '実行結果（JSON）';
COMMENT ON COLUMN job_executions.error_message IS 'エラー時のメッセージ';
COMMENT ON COLUMN job_executions.created_at IS '作成日時';

CREATE INDEX idx_job_executions_type_created ON job_executions(job_type, created_at DESC);
