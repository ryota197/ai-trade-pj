# データベース設計

## 概要

PostgreSQL 16 を使用。Docker コンテナで起動。

---

## テーブル一覧

| テーブル名 | 説明 | 主な用途 |
|-----------|------|---------|
| market_snapshots | マーケット状態の履歴 | マーケット分析、トレンド確認 |
| screener_results | スクリーニング結果のキャッシュ | スクリーニングの高速化 |
| watchlist | ウォッチリスト | 監視銘柄の管理 |
| paper_trades | ペーパートレード記録 | 仮想売買の記録 |
| price_cache | 株価キャッシュ | API呼び出し削減 |

---

## テーブル定義

### market_snapshots

マーケット状態の履歴を保存。日次でスナップショットを取得。

```sql
CREATE TABLE market_snapshots (
    id SERIAL PRIMARY KEY,
    recorded_at TIMESTAMP NOT NULL,

    -- VIX関連
    vix DECIMAL(10,2),
    vix_change DECIMAL(10,2),

    -- Put/Call Ratio
    put_call_ratio DECIMAL(10,4),

    -- 騰落レシオ
    advancing_issues INTEGER,
    declining_issues INTEGER,
    advance_decline_ratio DECIMAL(10,4),

    -- S&P500指標
    sp500_close DECIMAL(10,2),
    sp500_rsi DECIMAL(10,2),
    sp500_above_200ma BOOLEAN,
    sp500_distance_from_200ma DECIMAL(10,2),

    -- 判定結果
    market_status VARCHAR(20) NOT NULL,  -- 'risk_on', 'risk_off', 'neutral'
    confidence DECIMAL(5,2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_market_status CHECK (market_status IN ('risk_on', 'risk_off', 'neutral'))
);

-- インデックス
CREATE INDEX idx_market_snapshots_recorded_at ON market_snapshots(recorded_at DESC);
```

### screener_results

CAN-SLIMスクリーニング結果をキャッシュ。

```sql
CREATE TABLE screener_results (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    screened_at TIMESTAMP NOT NULL,

    -- 銘柄基本情報
    name VARCHAR(100),
    industry VARCHAR(50),
    market_cap BIGINT,

    -- 株価情報
    price DECIMAL(10,2),
    change_percent DECIMAL(10,2),
    volume BIGINT,
    avg_volume_50d BIGINT,

    -- CAN-SLIM指標
    eps_growth_q DECIMAL(10,2),       -- C: 四半期EPS成長率
    eps_growth_y DECIMAL(10,2),       -- A: 年間EPS成長率
    distance_from_high DECIMAL(10,2), -- N: 52週高値からの乖離
    volume_ratio DECIMAL(10,2),       -- S: 出来高倍率
    rs_rating DECIMAL(10,2),          -- L: RS Rating
    institutional_holding DECIMAL(10,2), -- I: 機関投資家保有率

    -- 判定結果
    passes_canslim BOOLEAN DEFAULT FALSE,
    canslim_score INTEGER,  -- 総合スコア（0-100）

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_symbol_screened UNIQUE (symbol, screened_at)
);

-- インデックス
CREATE INDEX idx_screener_results_symbol ON screener_results(symbol);
CREATE INDEX idx_screener_results_screened_at ON screener_results(screened_at DESC);
CREATE INDEX idx_screener_results_passes ON screener_results(passes_canslim, screened_at DESC);
CREATE INDEX idx_screener_results_rs_rating ON screener_results(rs_rating DESC);
```

### watchlist

ウォッチリスト。監視したい銘柄を登録。

```sql
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
    pattern_detected VARCHAR(50),  -- 検出されたパターン
    alert_enabled BOOLEAN DEFAULT TRUE,

    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX idx_watchlist_symbol ON watchlist(symbol);
```

### paper_trades

ペーパートレード（仮想売買）の記録。

```sql
CREATE TABLE paper_trades (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,

    -- トレード情報
    trade_type VARCHAR(10) NOT NULL,  -- 'buy', 'sell'
    quantity INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(12,2) GENERATED ALWAYS AS (quantity * price) STORED,

    -- 実行日時
    traded_at TIMESTAMP NOT NULL,

    -- 関連情報
    notes TEXT,
    strategy VARCHAR(50),  -- 'breakout', 'pullback', 'swing' etc.

    -- ポジション管理用
    position_id UUID,  -- 同一ポジションのbuy/sellを紐付け

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_trade_type CHECK (trade_type IN ('buy', 'sell')),
    CONSTRAINT positive_quantity CHECK (quantity > 0),
    CONSTRAINT positive_price CHECK (price > 0)
);

-- インデックス
CREATE INDEX idx_paper_trades_symbol ON paper_trades(symbol);
CREATE INDEX idx_paper_trades_traded_at ON paper_trades(traded_at DESC);
CREATE INDEX idx_paper_trades_position ON paper_trades(position_id);
```

### price_cache

株価データのキャッシュ。yfinance API呼び出しを削減。

```sql
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

-- インデックス
CREATE INDEX idx_price_cache_symbol_date ON price_cache(symbol, date DESC);
```

---

## ER図

```
┌─────────────────────┐
│  market_snapshots   │
├─────────────────────┤
│ id (PK)             │
│ recorded_at         │
│ vix                 │
│ put_call_ratio      │
│ sp500_rsi           │
│ market_status       │
│ ...                 │
└─────────────────────┘

┌─────────────────────┐
│  screener_results   │
├─────────────────────┤
│ id (PK)             │
│ symbol              │───┐
│ screened_at         │   │
│ eps_growth_q        │   │
│ rs_rating           │   │
│ passes_canslim      │   │
│ ...                 │   │
└─────────────────────┘   │
                          │ symbol
┌─────────────────────┐   │
│     watchlist       │   │
├─────────────────────┤   │
│ id (PK)             │   │
│ symbol (UNIQUE)     │◄──┤
│ target_entry_price  │   │
│ stop_loss_price     │   │
│ notes               │   │
│ ...                 │   │
└─────────────────────┘   │
                          │
┌─────────────────────┐   │
│   paper_trades      │   │
├─────────────────────┤   │
│ id (PK)             │   │
│ symbol              │◄──┤
│ trade_type          │   │
│ quantity            │   │
│ price               │   │
│ traded_at           │   │
│ position_id         │   │
│ ...                 │   │
└─────────────────────┘   │
                          │
┌─────────────────────┐   │
│    price_cache      │   │
├─────────────────────┤   │
│ id (PK)             │   │
│ symbol              │◄──┘
│ date                │
│ open/high/low/close │
│ volume              │
│ ...                 │
└─────────────────────┘
```

※ symbol での論理的な関連はあるが、外部キー制約は設けない（柔軟性重視）

---

## マイグレーション

### 初期セットアップ

```sql
-- init.sql
-- Docker起動時に自動実行される

-- 拡張機能
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- テーブル作成（上記DDLを順次実行）
```

### Docker Compose設定

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: trader
      POSTGRES_PASSWORD: localdev
      POSTGRES_DB: trading
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
```

---

## インデックス設計方針

| 目的 | インデックス |
|-----|-------------|
| 時系列クエリ | `recorded_at DESC`, `traded_at DESC` |
| シンボル検索 | `symbol` |
| スクリーニング | `passes_canslim`, `rs_rating DESC` |
| 複合検索 | `(symbol, date)` |

---

## データ保持ポリシー

| テーブル | 保持期間 | 理由 |
|---------|---------|------|
| market_snapshots | 無期限 | 過去のマーケット分析に使用 |
| screener_results | 30日 | 最新データのみ必要 |
| watchlist | 無期限 | ユーザーデータ |
| paper_trades | 無期限 | パフォーマンス分析に使用 |
| price_cache | 2年 | 長期チャート分析用 |

### クリーンアップジョブ（将来実装）

```sql
-- 古いスクリーニング結果を削除
DELETE FROM screener_results
WHERE screened_at < NOW() - INTERVAL '30 days';

-- 古い株価キャッシュを削除
DELETE FROM price_cache
WHERE date < NOW() - INTERVAL '2 years';
```
