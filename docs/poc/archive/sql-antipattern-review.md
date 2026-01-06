# SQLアンチパターン レビュー

## 目的

現在のDB設計を「SQLアンチパターン」の観点から評価し、改善案を記録する。

---

## 1. 現状の設計に該当するアンチパターン

### 1.1 IDリクワイアド（ID Required）

**概要:** すべてのテーブルに機械的にサロゲートキー（id）を追加するパターン。

**該当箇所:** `stock_prices`, `stock_metrics` の `id` カラム

```sql
-- 現状
CREATE TABLE stock_prices (
    id SERIAL PRIMARY KEY,  -- ← 本当に必要？
    symbol VARCHAR(10),
    recorded_at TIMESTAMP,
    ...
);
```

**問題点:**
- 自然キー `(symbol, date)` で一意に特定可能
- 不要なサロゲートキーはストレージと索引のオーバーヘッド
- JOINが複雑になる可能性

**改善案:**
```sql
CREATE TABLE stock_snapshots (
    symbol VARCHAR(10),
    date DATE,
    PRIMARY KEY (symbol, date),  -- 複合主キー
    ...
);
```

---

### 1.2 キーレスエントリ（Keyless Entry）

**概要:** 外部キー制約を定義しない、または不十分なパターン。

**該当箇所:** `stock_prices.symbol`, `stock_metrics.symbol`

**問題点:**
- 参照整合性が保証されない
- 親レコード削除時に孤立データが発生
- アプリケーション側での整合性チェックが必要

**改善案:**
```sql
CREATE TABLE stock_snapshots (
    symbol VARCHAR(10) REFERENCES stocks(symbol) ON DELETE CASCADE,
    ...
);
```

---

### 1.3 EAV（Entity-Attribute-Value）の兆候

**概要:** 汎用的すぎるテーブル設計。属性名と値をカラムではなく行として格納。

**該当箇所:** `screener_results.canslim_detail` (JSON)

```python
# 現状のコード
canslim_detail = json.dumps(entity.canslim_score.to_dict())
# {"c_score": 80, "a_score": 75, "n_score": 60, ...}
```

**問題点:**
- クエリが複雑（`->>` 演算子、JSONB関数）
- インデックスが効きにくい（GINインデックスは可能だが制限あり）
- スキーマ検証がDB側でできない
- 型安全性がない

**改善案:**
```sql
CREATE TABLE stock_ratings (
    ...
    canslim_score INTEGER,
    -- CAN-SLIM内訳を個別カラム化
    score_c INTEGER,  -- Current Earnings
    score_a INTEGER,  -- Annual Earnings
    score_n INTEGER,  -- New Product/Management
    score_s INTEGER,  -- Supply/Demand
    score_l INTEGER,  -- Leader/Laggard
    score_i INTEGER,  -- Institutional Sponsorship
    score_m INTEGER,  -- Market Direction
    ...
);
```

---

### 1.4 スパゲッティクエリ（Spaghetti Query）の予兆

**概要:** 複雑すぎるクエリ。多数のJOIN、サブクエリ、条件が絡み合う。

**該当箇所:** `postgres_stock_query_repository.py:81-89`

```python
# 現状
stmt = (
    select(StockModel, StockPriceModel, StockMetricsModel)
    .join(StockPriceModel, StockModel.symbol == StockPriceModel.symbol)
    .join(StockMetricsModel, StockModel.symbol == StockMetricsModel.symbol)
    .where(func.date(StockPriceModel.recorded_at) == today)
    .where(func.date(StockMetricsModel.calculated_at) == today)
    .where(StockMetricsModel.rs_rating.isnot(None))
    .where(StockMetricsModel.canslim_score.isnot(None))
    # + 追加フィルター条件...
)
```

**問題点:**
- 3テーブルJOIN + 複数条件
- 可読性が低い
- フィルター追加で更に複雑化
- デバッグが困難

**改善案:**
- ビューまたはマテリアライズドビューで抽象化
- テーブル設計の見直しでJOIN削減

---

### 1.5 過剰な正規化（Over-Normalization）

**概要:** 正規化を過度に適用し、不必要なJOINを増やすパターン。

**該当箇所:** `stocks` テーブル（マスター）の分離

```sql
-- 現状: マスターテーブルを分離
CREATE TABLE stocks (
    symbol VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100),      -- ← ほぼ不変
    industry VARCHAR(50),   -- ← ほぼ不変
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 毎回JOINが必要
SELECT s.symbol, s.name, s.industry, p.price, m.rs_rating
FROM stocks s
JOIN stock_prices p ON s.symbol = p.symbol
JOIN stock_metrics m ON s.symbol = m.symbol
WHERE ...
```

**stocksテーブルから取得するカラム:**

| カラム | 更新頻度 | 用途 |
|--------|---------|------|
| symbol | 不変 | 主キー（全テーブルに既に存在） |
| name | ほぼ不変 | 表示用 |
| industry | ほぼ不変 | 表示・フィルター用 |

**問題点:**
- `name` と `industry` のためだけに毎回JOINが発生
- これらの値はほぼ変更されない（マスターデータ）
- 正規化のメリット（更新の一元化）が活かされていない

**判断基準:**

| 質問 | 回答 | 判定 |
|------|------|------|
| name/industryは頻繁に変わる？ | ほぼ変わらない | 非正規化OK |
| 変更時に即座反映が必要？ | 日次更新で十分 | 非正規化OK |
| 銘柄数は？ | ~500（S&P500） | どちらでも可 |

**改善案:**

```sql
-- Option 1: stocksテーブル廃止、snapshotsに統合
CREATE TABLE stock_snapshots (
    symbol VARCHAR(10),
    date DATE,
    name VARCHAR(100),        -- ← 統合
    industry VARCHAR(50),      -- ← 統合
    price DECIMAL(10,2),
    ...
    PRIMARY KEY (symbol, date)
);

-- Option 2: 全統合（POC向け、最シンプル）
CREATE TABLE stocks_daily (
    symbol VARCHAR(10),
    date DATE,
    name VARCHAR(100),
    industry VARCHAR(50),
    price DECIMAL(10,2),
    rs_rating INTEGER,
    canslim_score INTEGER,
    ...
    PRIMARY KEY (symbol, date)
);
```

**推奨:**

| フェーズ | 推奨 | 理由 |
|---------|------|------|
| POC | Option 2（全統合） | シンプル最優先 |
| MVP | Option 1 + ビュー | 拡張性を考慮 |
| 本番 | 要件次第 | 銘柄数・更新頻度による |

---

## 2. 該当しないアンチパターン（確認済み）

| アンチパターン | 状況 |
|---------------|------|
| ジェイウォーク | カンマ区切りリストなし ✓ |
| マルチカラム属性 | 同種カラムの重複なし ✓ |
| ポリモーフィック関連 | 複数テーブル参照なし ✓ |
| メタデータトリブル | テーブル名にデータなし ✓ |
| 31フレーバー | ENUM乱用なし ✓ |

---

## 3. 改善後の設計案（Option C 改良版）

### 3.1 テーブル定義

```sql
-- マスター（変更頻度: 低）
CREATE TABLE stocks (
    symbol VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 外部取得データ（変更頻度: 日次）
CREATE TABLE stock_snapshots (
    symbol VARCHAR(10) REFERENCES stocks(symbol) ON DELETE CASCADE,
    date DATE,
    -- 価格データ
    price DECIMAL(10,2),
    change_percent DECIMAL(5,2),
    volume BIGINT,
    avg_volume_50d BIGINT,
    market_cap BIGINT,
    week_52_high DECIMAL(10,2),
    week_52_low DECIMAL(10,2),
    -- 財務データ（外部API取得）
    eps_growth_quarterly DECIMAL(10,2),
    eps_growth_annual DECIMAL(10,2),
    institutional_ownership DECIMAL(5,2),
    -- メタデータ
    fetched_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (symbol, date)
);

-- 内部計算データ（変更頻度: 日次、Job依存）
CREATE TABLE stock_ratings (
    symbol VARCHAR(10) REFERENCES stocks(symbol) ON DELETE CASCADE,
    date DATE,
    -- RS関連（Job 1, 2）
    relative_strength DECIMAL(10,4),
    rs_rating INTEGER CHECK (rs_rating BETWEEN 1 AND 99),
    -- CAN-SLIM総合スコア（Job 3）
    canslim_score INTEGER CHECK (canslim_score BETWEEN 0 AND 100),
    -- CAN-SLIM内訳（EAV回避）
    score_c INTEGER,  -- Current Earnings
    score_a INTEGER,  -- Annual Earnings
    score_n INTEGER,  -- New Product/Management
    score_s INTEGER,  -- Supply/Demand
    score_l INTEGER,  -- Leader/Laggard
    score_i INTEGER,  -- Institutional Sponsorship
    score_m INTEGER,  -- Market Direction
    -- メタデータ
    calculated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (symbol, date)
);

-- インデックス
CREATE INDEX idx_stock_snapshots_date ON stock_snapshots(date);
CREATE INDEX idx_stock_ratings_date ON stock_ratings(date);
CREATE INDEX idx_stock_ratings_rs ON stock_ratings(rs_rating) WHERE rs_rating IS NOT NULL;
CREATE INDEX idx_stock_ratings_canslim ON stock_ratings(canslim_score) WHERE canslim_score IS NOT NULL;
```

### 3.2 ビュー定義（スパゲッティクエリ回避）

```sql
-- 最新データ用ビュー
CREATE VIEW stocks_current AS
SELECT
    s.symbol,
    s.name,
    s.industry,
    -- 価格データ
    snap.price,
    snap.change_percent,
    snap.volume,
    snap.avg_volume_50d,
    snap.market_cap,
    snap.week_52_high,
    snap.week_52_low,
    -- 財務データ
    snap.eps_growth_quarterly,
    snap.eps_growth_annual,
    snap.institutional_ownership,
    -- レーティング
    r.relative_strength,
    r.rs_rating,
    r.canslim_score,
    r.score_c, r.score_a, r.score_n, r.score_s, r.score_l, r.score_i, r.score_m,
    -- メタデータ
    snap.date,
    snap.fetched_at,
    r.calculated_at
FROM stocks s
LEFT JOIN stock_snapshots snap ON s.symbol = snap.symbol
LEFT JOIN stock_ratings r ON s.symbol = r.symbol AND snap.date = r.date
WHERE snap.date = CURRENT_DATE;

-- スクリーニング用ビュー（フィルター条件付き）
CREATE VIEW stocks_screener AS
SELECT * FROM stocks_current
WHERE rs_rating IS NOT NULL
  AND canslim_score IS NOT NULL;
```

---

## 4. アンチパターン対策まとめ

| アンチパターン | 対策 | 実装 |
|---------------|------|------|
| IDリクワイアド | 複合主キー採用 | `PRIMARY KEY (symbol, date)` |
| キーレスエントリ | FK制約明示 | `REFERENCES stocks(symbol)` |
| EAV | 個別カラム化 | `score_c`, `score_a`, ... |
| スパゲッティクエリ | ビューで抽象化 | `stocks_current`, `stocks_screener` |
| 過剰な正規化 | テーブル統合 | `stocks` 廃止、`stock_snapshots` に統合 |

---

## 5. 参考

- 書籍: 「SQLアンチパターン」Bill Karwin著
- 関連ドキュメント: `docs/poc/refactoring/db-redesign-analysis.md`
