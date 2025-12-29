# データベース設計

## 概要

PostgreSQL 16 を使用。Docker コンテナで起動。

---

## テーブル一覧

| テーブル名 | 説明 | 主な用途 |
|-----------|------|---------|
| stocks | 銘柄データ | スクリーニング結果、CAN-SLIM指標 |
| market_snapshots | マーケット状態の履歴 | マーケット分析、トレンド確認 |
| watchlist | ウォッチリスト | 監視銘柄の管理 |
| paper_trades | ペーパートレード記録 | 仮想売買の記録 |
| price_cache | 株価キャッシュ | API呼び出し削減 |
| job_executions | ジョブ実行履歴 | バッチ処理の実行記録 |

---

## テーブル定義

### stocks

銘柄のスクリーニングデータを保存。CAN-SLIM指標を含む。

| カラム | 型 | NULL | 説明 |
|-------|-----|------|------|
| id | SERIAL | NO | 主キー |
| symbol | VARCHAR(10) | NO | ティッカーシンボル（UNIQUE） |
| name | VARCHAR(100) | YES | 銘柄名 |
| industry | VARCHAR(50) | YES | 業種 |
| market_cap | BIGINT | YES | 時価総額 |
| price | DECIMAL(10,2) | YES | 現在株価 |
| change_percent | DECIMAL(10,2) | YES | 変動率 |
| volume | BIGINT | YES | 出来高 |
| avg_volume_50d | BIGINT | YES | 50日平均出来高 |
| week_52_high | DECIMAL(10,2) | YES | 52週高値 |
| week_52_low | DECIMAL(10,2) | YES | 52週安値 |
| eps_growth_quarterly | DECIMAL(10,2) | YES | C: 四半期EPS成長率 |
| eps_growth_annual | DECIMAL(10,2) | YES | A: 年間EPS成長率 |
| institutional_ownership | DECIMAL(10,2) | YES | I: 機関投資家保有率 |
| relative_strength | DECIMAL(10,4) | YES | S&P500比の相対強度（生値） |
| rs_rating | INTEGER | YES | L: RS Rating（1-99パーセンタイル） |
| canslim_score | INTEGER | YES | CAN-SLIMスコア（0-100） |
| updated_at | TIMESTAMP | NO | 最終更新日時 |
| created_at | TIMESTAMP | NO | 作成日時 |

**備考:**
- `relative_strength`: 外部APIから計算した生値。Job 1 で保存。
- `rs_rating`: 全銘柄の `relative_strength` からパーセンタイル計算。Job 2 で更新。
- `canslim_score`: 各指標から総合スコア計算。Job 3 で更新。

---

### market_snapshots

マーケット状態の履歴を保存。定期的にスナップショットを取得。

| カラム | 型 | NULL | 説明 |
|-------|-----|------|------|
| id | SERIAL | NO | 主キー |
| recorded_at | TIMESTAMP | NO | 記録日時 |
| vix | DECIMAL(10,2) | NO | VIX指数 |
| vix_signal | VARCHAR(20) | NO | VIXシグナル（bullish/neutral/bearish） |
| sp500_price | DECIMAL(12,2) | NO | S&P500株価 |
| sp500_rsi | DECIMAL(5,2) | NO | S&P500 RSI（14日） |
| sp500_rsi_signal | VARCHAR(20) | NO | RSIシグナル |
| sp500_ma200 | DECIMAL(12,2) | NO | S&P500 200日移動平均 |
| sp500_above_ma200 | BOOLEAN | NO | 200MA上か |
| put_call_ratio | DECIMAL(6,4) | NO | プット/コール比率 |
| put_call_signal | VARCHAR(20) | NO | P/Cシグナル |
| market_condition | VARCHAR(20) | NO | 判定結果（risk_on/risk_off/neutral） |
| confidence | DECIMAL(5,4) | NO | 信頼度 |
| score | INTEGER | NO | スコア（-5〜+5） |
| recommendation | VARCHAR(500) | NO | 推奨アクション |
| created_at | TIMESTAMP | NO | 作成日時 |

---

### watchlist

ウォッチリスト。監視したい銘柄を登録。

| カラム | 型 | NULL | 説明 |
|-------|-----|------|------|
| id | SERIAL | NO | 主キー |
| symbol | VARCHAR(10) | NO | ティッカーシンボル（UNIQUE） |
| target_entry_price | DECIMAL(10,2) | YES | 目標エントリー価格 |
| stop_loss_price | DECIMAL(10,2) | YES | ストップロス価格 |
| target_profit_price | DECIMAL(10,2) | YES | 利確目標価格 |
| notes | TEXT | YES | メモ |
| pattern_detected | VARCHAR(50) | YES | 検出されたパターン |
| alert_enabled | BOOLEAN | NO | アラート有効 |
| added_at | TIMESTAMP | NO | 追加日時 |
| updated_at | TIMESTAMP | NO | 更新日時 |

---

### paper_trades

ペーパートレード（仮想売買）の記録。

| カラム | 型 | NULL | 説明 |
|-------|-----|------|------|
| id | SERIAL | NO | 主キー |
| symbol | VARCHAR(10) | NO | ティッカーシンボル |
| trade_type | VARCHAR(10) | NO | 売買種別（buy/sell） |
| quantity | INTEGER | NO | 数量 |
| entry_price | DECIMAL(10,2) | NO | エントリー価格 |
| exit_price | DECIMAL(10,2) | YES | 決済価格 |
| status | VARCHAR(20) | NO | ステータス（open/closed/cancelled） |
| traded_at | TIMESTAMP | NO | 取引日時 |
| closed_at | TIMESTAMP | YES | 決済日時 |
| notes | TEXT | YES | メモ |
| strategy | VARCHAR(50) | YES | 戦略（breakout/pullback等） |
| created_at | TIMESTAMP | NO | 作成日時 |

---

### price_cache

株価データのキャッシュ。外部API呼び出しを削減。

| カラム | 型 | NULL | 説明 |
|-------|-----|------|------|
| id | SERIAL | NO | 主キー |
| symbol | VARCHAR(10) | NO | ティッカーシンボル |
| date | DATE | NO | 日付 |
| open | DECIMAL(10,2) | YES | 始値 |
| high | DECIMAL(10,2) | YES | 高値 |
| low | DECIMAL(10,2) | YES | 安値 |
| close | DECIMAL(10,2) | YES | 終値 |
| adj_close | DECIMAL(10,2) | YES | 調整後終値 |
| volume | BIGINT | YES | 出来高 |
| created_at | TIMESTAMP | NO | 作成日時 |

**制約:** `(symbol, date)` でユニーク

---

### job_executions

ジョブ実行履歴。完了時に1レコード INSERT。

| カラム | 型 | NULL | 説明 |
|-------|-----|------|------|
| id | UUID | NO | ジョブID（PK） |
| job_type | VARCHAR(50) | NO | ジョブ種別（refresh_screener等） |
| status | VARCHAR(20) | NO | 結果（completed/failed） |
| started_at | TIMESTAMP | NO | 開始日時 |
| completed_at | TIMESTAMP | NO | 完了日時 |
| duration_seconds | INTEGER | NO | 実行時間（秒） |
| result | JSONB | YES | 実行結果 |
| error_message | TEXT | YES | エラー時のメッセージ |
| created_at | TIMESTAMP | NO | 作成日時 |

**備考:**
- ジョブ完了時に1回だけ INSERT（進捗更新なし）
- `result` 例: `{"succeeded": 498, "failed": 2, "errors": [...]}`

---

## ER図

```
┌─────────────────────┐
│       stocks        │
├─────────────────────┤
│ id (PK)             │
│ symbol (UNIQUE)     │───┐
│ name                │   │
│ price               │   │
│ relative_strength   │   │
│ rs_rating           │   │
│ canslim_score       │   │
│ ...                 │   │
└─────────────────────┘   │
                          │
┌─────────────────────┐   │
│  market_snapshots   │   │
├─────────────────────┤   │
│ id (PK)             │   │
│ recorded_at         │   │
│ vix                 │   │
│ market_condition    │   │
│ ...                 │   │
└─────────────────────┘   │
                          │ symbol (論理関連)
┌─────────────────────┐   │
│     watchlist       │   │
├─────────────────────┤   │
│ id (PK)             │   │
│ symbol (UNIQUE)     │◄──┤
│ target_entry_price  │   │
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
│ ...                 │   │
└─────────────────────┘   │
                          │
┌─────────────────────┐   │
│    price_cache      │   │
├─────────────────────┤   │
│ id (PK)             │   │
│ symbol              │◄──┘
│ date                │
│ OHLCV               │
└─────────────────────┘

┌─────────────────────┐
│   job_executions     │
├─────────────────────┤
│ id (PK, UUID)       │
│ job_type            │
│ status              │
│ started_at          │
│ completed_at        │
│ result (JSONB)      │
└─────────────────────┘
```

※ symbol での論理的な関連はあるが、外部キー制約は設けない（柔軟性重視）
※ job_executions は他テーブルとの関連なし（独立した履歴テーブル）

---

## インデックス設計

| テーブル | インデックス | 目的 |
|---------|-------------|------|
| stocks | symbol | シンボル検索 |
| stocks | rs_rating DESC | スクリーニング順位 |
| stocks | canslim_score DESC | スコア順ソート |
| market_snapshots | recorded_at DESC | 時系列クエリ |
| watchlist | symbol | シンボル検索 |
| paper_trades | symbol | シンボル検索 |
| paper_trades | traded_at DESC | 時系列クエリ |
| paper_trades | status | ステータス絞り込み |
| price_cache | (symbol, date) DESC | 銘柄×日付の複合検索 |
| job_executions | job_type, created_at DESC | ジョブ種別×日時検索 |

---

## データ保持ポリシー

| テーブル | 保持期間 | 理由 |
|---------|---------|------|
| stocks | 無期限 | スクリーニングデータ |
| market_snapshots | 無期限 | 過去のマーケット分析に使用 |
| watchlist | 無期限 | ユーザーデータ |
| paper_trades | 無期限 | パフォーマンス分析に使用 |
| price_cache | 2年 | 長期チャート分析用 |
| job_executions | 90日 | 直近の実行履歴のみ必要 |

---

## 関連ドキュメント

- `backend/src/infrastructure/database/init.sql` - DDL定義
- `docs/poc/plan/refresh-screener-usecase.md` - ジョブ設計（stocks更新）
