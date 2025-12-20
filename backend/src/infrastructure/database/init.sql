-- init.sql
-- Docker起動時に自動実行される初期化スクリプト

-- 拡張機能
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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

COMMENT ON TABLE market_snapshots IS 'マーケット状態の履歴スナップショット（1時間ごと）';
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
-- screener_results: CAN-SLIMスクリーニング結果キャッシュ
-- =====================================================
CREATE TABLE screener_results (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,

    -- 銘柄基本情報
    name VARCHAR(200) NOT NULL,

    -- 株価情報
    price DECIMAL(12,2) NOT NULL,
    change_percent DECIMAL(8,2) NOT NULL,
    volume INTEGER NOT NULL,
    avg_volume INTEGER NOT NULL,
    market_cap DECIMAL(20,2),
    pe_ratio DECIMAL(10,2),
    week_52_high DECIMAL(12,2) NOT NULL,
    week_52_low DECIMAL(12,2) NOT NULL,

    -- CAN-SLIM指標
    eps_growth_quarterly DECIMAL(8,2),
    eps_growth_annual DECIMAL(8,2),
    rs_rating INTEGER NOT NULL,
    institutional_ownership DECIMAL(6,2),

    -- CAN-SLIMスコア
    canslim_total_score INTEGER NOT NULL,
    canslim_detail TEXT,

    -- メタデータ
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_screener_symbol UNIQUE (symbol)
);

COMMENT ON TABLE screener_results IS 'CAN-SLIMスクリーニング結果のキャッシュ';
COMMENT ON COLUMN screener_results.symbol IS 'ティッカーシンボル（例: AAPL）';
COMMENT ON COLUMN screener_results.name IS '企業名';
COMMENT ON COLUMN screener_results.price IS '株価';
COMMENT ON COLUMN screener_results.change_percent IS '前日比変動率（%）';
COMMENT ON COLUMN screener_results.volume IS '出来高';
COMMENT ON COLUMN screener_results.avg_volume IS '平均出来高';
COMMENT ON COLUMN screener_results.market_cap IS '時価総額（USD）';
COMMENT ON COLUMN screener_results.pe_ratio IS 'PER';
COMMENT ON COLUMN screener_results.week_52_high IS '52週高値';
COMMENT ON COLUMN screener_results.week_52_low IS '52週安値';
COMMENT ON COLUMN screener_results.eps_growth_quarterly IS 'C: 四半期EPS成長率（%）';
COMMENT ON COLUMN screener_results.eps_growth_annual IS 'A: 年間EPS成長率（%）';
COMMENT ON COLUMN screener_results.rs_rating IS 'L: RS Rating（1-99）';
COMMENT ON COLUMN screener_results.institutional_ownership IS 'I: 機関投資家保有率（%）';
COMMENT ON COLUMN screener_results.canslim_total_score IS 'CAN-SLIMスコア（0-100）';
COMMENT ON COLUMN screener_results.canslim_detail IS 'CAN-SLIMスコア詳細（JSON）';
COMMENT ON COLUMN screener_results.updated_at IS '最終更新日時';
COMMENT ON COLUMN screener_results.created_at IS '作成日時';

CREATE INDEX idx_screener_results_symbol ON screener_results(symbol);
CREATE INDEX idx_screener_results_rs_rating ON screener_results(rs_rating DESC);
CREATE INDEX idx_screener_results_canslim_score ON screener_results(canslim_total_score DESC);
CREATE INDEX idx_screener_results_updated_at ON screener_results(updated_at DESC);

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

    -- メモ
    notes TEXT,

    -- 追加情報
    pattern_detected VARCHAR(50),
    alert_enabled BOOLEAN DEFAULT TRUE,

    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE watchlist IS '監視銘柄リスト';
COMMENT ON COLUMN watchlist.symbol IS 'ティッカーシンボル';
COMMENT ON COLUMN watchlist.target_entry_price IS 'エントリー目標価格';
COMMENT ON COLUMN watchlist.stop_loss_price IS 'ストップロス価格';
COMMENT ON COLUMN watchlist.target_profit_price IS '利確目標価格';
COMMENT ON COLUMN watchlist.notes IS 'メモ（エントリー理由など）';
COMMENT ON COLUMN watchlist.pattern_detected IS '検出されたチャートパターン';
COMMENT ON COLUMN watchlist.alert_enabled IS 'アラート有効フラグ';
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
    price DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(12,2) GENERATED ALWAYS AS (quantity * price) STORED,

    -- 実行日時
    traded_at TIMESTAMP NOT NULL,

    -- 関連情報
    notes TEXT,
    strategy VARCHAR(50),

    -- ポジション管理用
    position_id UUID,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_trade_type CHECK (trade_type IN ('buy', 'sell')),
    CONSTRAINT positive_quantity CHECK (quantity > 0),
    CONSTRAINT positive_price CHECK (price > 0)
);

COMMENT ON TABLE paper_trades IS 'ペーパートレード（仮想売買）記録';
COMMENT ON COLUMN paper_trades.symbol IS 'ティッカーシンボル';
COMMENT ON COLUMN paper_trades.trade_type IS '売買種別: buy/sell';
COMMENT ON COLUMN paper_trades.quantity IS '数量（株数）';
COMMENT ON COLUMN paper_trades.price IS '約定価格';
COMMENT ON COLUMN paper_trades.total_amount IS '約定金額（自動計算: quantity * price）';
COMMENT ON COLUMN paper_trades.traded_at IS '約定日時';
COMMENT ON COLUMN paper_trades.notes IS 'メモ（エントリー/エグジット理由）';
COMMENT ON COLUMN paper_trades.strategy IS '戦略: breakout/pullback/swing等';
COMMENT ON COLUMN paper_trades.position_id IS 'ポジションID（同一ポジションのbuy/sellを紐付け）';

CREATE INDEX idx_paper_trades_symbol ON paper_trades(symbol);
CREATE INDEX idx_paper_trades_traded_at ON paper_trades(traded_at DESC);
CREATE INDEX idx_paper_trades_position ON paper_trades(position_id);

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
