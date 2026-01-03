-- init.sql
-- Docker起動時に自動実行される初期化スクリプト
-- ドメインモデルに基づくスキーマ設計（docs/poc/domain/03-database-design.md 参照）

-- 拡張機能
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- canslim_stocks: CAN-SLIM分析銘柄（Screener Context）
-- ドメインモデル: CANSLIMStock 集約
-- =====================================================
CREATE TABLE canslim_stocks (
    -- 主キー（複合）
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,

    -- 銘柄情報
    name VARCHAR(100),
    industry VARCHAR(50),

    -- 価格データ（PriceSnapshot）
    price DECIMAL(10,2),
    change_percent DECIMAL(5,2),
    volume BIGINT,
    avg_volume_50d BIGINT,
    market_cap BIGINT,
    week_52_high DECIMAL(10,2),
    week_52_low DECIMAL(10,2),

    -- 財務データ
    eps_growth_quarterly DECIMAL(10,2),
    eps_growth_annual DECIMAL(10,2),
    institutional_ownership DECIMAL(5,2),

    -- RS関連（StockRating）
    relative_strength DECIMAL(10,4),
    rs_rating INTEGER,

    -- CAN-SLIMスコア（CANSLIMScore）
    canslim_score INTEGER,
    score_c INTEGER,
    score_a INTEGER,
    score_n INTEGER,
    score_s INTEGER,
    score_l INTEGER,
    score_i INTEGER,
    score_m INTEGER,

    -- メタデータ
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 制約
    PRIMARY KEY (symbol, date),
    CONSTRAINT valid_rs_rating CHECK (rs_rating IS NULL OR rs_rating BETWEEN 1 AND 99),
    CONSTRAINT valid_canslim CHECK (canslim_score IS NULL OR canslim_score BETWEEN 0 AND 100)
);

COMMENT ON TABLE canslim_stocks IS 'CAN-SLIM分析銘柄（1集約 = 1テーブル）';
COMMENT ON COLUMN canslim_stocks.symbol IS 'ティッカーシンボル（例: AAPL）';
COMMENT ON COLUMN canslim_stocks.date IS '記録日';
COMMENT ON COLUMN canslim_stocks.name IS '企業名';
COMMENT ON COLUMN canslim_stocks.industry IS '業種';
COMMENT ON COLUMN canslim_stocks.price IS '現在株価';
COMMENT ON COLUMN canslim_stocks.change_percent IS '前日比変動率（%）';
COMMENT ON COLUMN canslim_stocks.volume IS '出来高';
COMMENT ON COLUMN canslim_stocks.avg_volume_50d IS '50日平均出来高';
COMMENT ON COLUMN canslim_stocks.market_cap IS '時価総額（USD）';
COMMENT ON COLUMN canslim_stocks.week_52_high IS '52週高値';
COMMENT ON COLUMN canslim_stocks.week_52_low IS '52週安値';
COMMENT ON COLUMN canslim_stocks.eps_growth_quarterly IS 'C: 四半期EPS成長率（%）';
COMMENT ON COLUMN canslim_stocks.eps_growth_annual IS 'A: 年間EPS成長率（%）';
COMMENT ON COLUMN canslim_stocks.institutional_ownership IS 'I: 機関投資家保有率（%）';
COMMENT ON COLUMN canslim_stocks.relative_strength IS 'S&P500比の相対強度（生値）';
COMMENT ON COLUMN canslim_stocks.rs_rating IS 'L: RS Rating（1-99パーセンタイル）';
COMMENT ON COLUMN canslim_stocks.canslim_score IS 'CAN-SLIMスコア（0-100）';
COMMENT ON COLUMN canslim_stocks.score_c IS 'C: Current Earnings スコア';
COMMENT ON COLUMN canslim_stocks.score_a IS 'A: Annual Earnings スコア';
COMMENT ON COLUMN canslim_stocks.score_n IS 'N: New Product スコア';
COMMENT ON COLUMN canslim_stocks.score_s IS 'S: Supply/Demand スコア';
COMMENT ON COLUMN canslim_stocks.score_l IS 'L: Leader スコア';
COMMENT ON COLUMN canslim_stocks.score_i IS 'I: Institutional スコア';
COMMENT ON COLUMN canslim_stocks.score_m IS 'M: Market スコア';
COMMENT ON COLUMN canslim_stocks.updated_at IS '更新日時';

-- インデックス
CREATE INDEX idx_canslim_stocks_date ON canslim_stocks(date);
CREATE INDEX idx_canslim_stocks_rs ON canslim_stocks(rs_rating DESC)
    WHERE rs_rating IS NOT NULL;
CREATE INDEX idx_canslim_stocks_canslim ON canslim_stocks(canslim_score DESC)
    WHERE canslim_score IS NOT NULL;

-- =====================================================
-- market_snapshots: 市場状態スナップショット（Market Context）
-- ドメインモデル: MarketSnapshot 集約
-- =====================================================
CREATE TABLE market_snapshots (
    id SERIAL PRIMARY KEY,
    recorded_at TIMESTAMP NOT NULL,

    -- 指標
    vix DECIMAL(10,2) NOT NULL,
    sp500_price DECIMAL(12,2) NOT NULL,
    sp500_rsi DECIMAL(5,2) NOT NULL,
    sp500_ma200 DECIMAL(12,2) NOT NULL,
    put_call_ratio DECIMAL(6,4) NOT NULL,

    -- 判定結果
    condition VARCHAR(20) NOT NULL,
    score INTEGER NOT NULL,

    -- 制約
    CONSTRAINT valid_condition CHECK (condition IN ('risk_on', 'neutral', 'risk_off')),
    CONSTRAINT valid_score CHECK (score BETWEEN -5 AND 5)
);

COMMENT ON TABLE market_snapshots IS '市場状態スナップショット';
COMMENT ON COLUMN market_snapshots.recorded_at IS 'スナップショット取得日時';
COMMENT ON COLUMN market_snapshots.vix IS 'VIX指数（恐怖指数）';
COMMENT ON COLUMN market_snapshots.sp500_price IS 'S&P500現在価格';
COMMENT ON COLUMN market_snapshots.sp500_rsi IS 'S&P500のRSI（14日）';
COMMENT ON COLUMN market_snapshots.sp500_ma200 IS 'S&P500の200日移動平均';
COMMENT ON COLUMN market_snapshots.put_call_ratio IS 'Put/Call Ratio';
COMMENT ON COLUMN market_snapshots.condition IS '判定結果: risk_on/neutral/risk_off';
COMMENT ON COLUMN market_snapshots.score IS '総合スコア（-5〜+5）';

CREATE INDEX idx_market_snapshots_recorded ON market_snapshots(recorded_at DESC);

-- =====================================================
-- watchlist: ウォッチリスト（Portfolio Context）
-- ドメインモデル: WatchlistItem 集約
-- =====================================================
CREATE TABLE watchlist (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,

    -- 目標価格
    target_entry_price DECIMAL(10,2),
    stop_loss_price DECIMAL(10,2),
    target_profit_price DECIMAL(10,2),

    -- メモ
    notes TEXT,

    -- タイムスタンプ
    added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE watchlist IS 'ウォッチリスト';
COMMENT ON COLUMN watchlist.symbol IS 'ティッカーシンボル';
COMMENT ON COLUMN watchlist.target_entry_price IS 'エントリー目標価格';
COMMENT ON COLUMN watchlist.stop_loss_price IS 'ストップロス価格';
COMMENT ON COLUMN watchlist.target_profit_price IS '利確目標価格';
COMMENT ON COLUMN watchlist.notes IS 'メモ';
COMMENT ON COLUMN watchlist.added_at IS '追加日時';
COMMENT ON COLUMN watchlist.updated_at IS '更新日時';

CREATE INDEX idx_watchlist_symbol ON watchlist(symbol);

-- =====================================================
-- trades: ペーパートレード（Portfolio Context）
-- ドメインモデル: Trade 集約
-- =====================================================
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,

    -- トレード情報
    trade_type VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,
    entry_price DECIMAL(10,2) NOT NULL,
    exit_price DECIMAL(10,2),

    -- ステータス
    status VARCHAR(20) NOT NULL DEFAULT 'open',

    -- タイムスタンプ
    traded_at TIMESTAMP NOT NULL,
    closed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 制約
    CONSTRAINT valid_trade_type CHECK (trade_type IN ('buy', 'sell')),
    CONSTRAINT valid_status CHECK (status IN ('open', 'closed', 'cancelled')),
    CONSTRAINT positive_quantity CHECK (quantity > 0),
    CONSTRAINT positive_entry CHECK (entry_price > 0)
);

COMMENT ON TABLE trades IS 'ペーパートレード';
COMMENT ON COLUMN trades.symbol IS 'ティッカーシンボル';
COMMENT ON COLUMN trades.trade_type IS '売買種別: buy/sell';
COMMENT ON COLUMN trades.quantity IS '数量（株数）';
COMMENT ON COLUMN trades.entry_price IS 'エントリー価格';
COMMENT ON COLUMN trades.exit_price IS '決済価格';
COMMENT ON COLUMN trades.status IS 'ステータス: open/closed/cancelled';
COMMENT ON COLUMN trades.traded_at IS '取引日時';
COMMENT ON COLUMN trades.closed_at IS '決済日時';
COMMENT ON COLUMN trades.created_at IS '作成日時';

CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_status ON trades(status);
CREATE INDEX idx_trades_traded_at ON trades(traded_at DESC);

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
COMMENT ON COLUMN job_executions.job_type IS 'ジョブ種別';
COMMENT ON COLUMN job_executions.status IS '結果: completed/failed';
COMMENT ON COLUMN job_executions.started_at IS '開始日時';
COMMENT ON COLUMN job_executions.completed_at IS '完了日時';
COMMENT ON COLUMN job_executions.duration_seconds IS '実行時間（秒）';
COMMENT ON COLUMN job_executions.result IS '実行結果（JSON）';
COMMENT ON COLUMN job_executions.error_message IS 'エラー時のメッセージ';
COMMENT ON COLUMN job_executions.created_at IS '作成日時';

CREATE INDEX idx_job_executions_type_created ON job_executions(job_type, created_at DESC);
