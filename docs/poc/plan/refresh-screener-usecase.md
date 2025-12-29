# スクリーニングデータ更新 設計書

## 概要

スクリーニングデータを更新するためのジョブ設計。
責務を明確に分離し、各ジョブが独立して実行可能な設計とする。

---

## 設計原則

1. **責務分離**: 1ジョブ = 1責務
2. **独立性**: 各銘柄の処理が他銘柄に影響しない
3. **再実行性**: 失敗時に該当ジョブのみ再実行可能
4. **正確性**: RS Ratingは常にDB全銘柄でパーセンタイル計算
5. **効率性**: ベンチマークデータは1日1回取得し再利用

---

## DBスキーマ（正規化設計）

### 設計方針

Stock エンティティを **更新頻度** と **責務** で正規化し、4テーブルに分離する。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            テーブル構成                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  stocks (マスター)          stock_prices (日次)       stock_metrics (計算)  │
│  ┌────────────────┐        ┌─────────────────┐       ┌─────────────────┐   │
│  │ symbol (PK)    │◄───────┤ symbol (FK)     │       │ symbol (FK)     │   │
│  │ name           │        │ price           │       │ eps_growth_q    │   │
│  │ industry       │        │ change_percent  │       │ eps_growth_a    │   │
│  │ created_at     │        │ volume          │       │ inst_ownership  │   │
│  └────────────────┘        │ avg_volume_50d  │       │ relative_strength│  │
│                            │ market_cap      │       │ rs_rating       │   │
│                            │ week_52_high    │       │ canslim_score   │   │
│                            │ week_52_low     │       │ calculated_at   │   │
│                            │ recorded_at     │       └─────────────────┘   │
│                            └─────────────────┘                              │
│                                                                             │
│  market_benchmarks (ベンチマーク)                                            │
│  ┌─────────────────────────┐                                                │
│  │ id (PK)                 │                                                │
│  │ symbol (^GSPC, ^NDX)    │                                                │
│  │ performance_1y          │                                                │
│  │ performance_6m          │                                                │
│  │ performance_3m          │                                                │
│  │ recorded_at             │                                                │
│  └─────────────────────────┘                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### テーブル定義

#### stocks（銘柄マスター）

```sql
CREATE TABLE stocks (
    symbol VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100),
    industry VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

- 更新頻度: 稀（企業情報変更時のみ）
- 用途: 銘柄の基本情報

#### stock_prices（価格スナップショット）

```sql
CREATE TABLE stock_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL REFERENCES stocks(symbol),
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

CREATE INDEX idx_stock_prices_symbol_date
    ON stock_prices(symbol, recorded_at DESC);
```

- 更新頻度: 日次（市場終了後）
- 用途: 株価・出来高のスナップショット
- 履歴保持: 日次で蓄積可能

#### stock_metrics（計算指標）

```sql
CREATE TABLE stock_metrics (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL REFERENCES stocks(symbol),

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

CREATE INDEX idx_stock_metrics_symbol_date
    ON stock_metrics(symbol, calculated_at DESC);
CREATE INDEX idx_stock_metrics_rs_rating
    ON stock_metrics(rs_rating DESC) WHERE rs_rating IS NOT NULL;
CREATE INDEX idx_stock_metrics_canslim
    ON stock_metrics(canslim_score DESC) WHERE canslim_score IS NOT NULL;
```

- 更新頻度: Job実行時
- 用途: CAN-SLIM関連の計算指標
- 履歴保持: 計算履歴として蓄積可能

#### market_benchmarks（市場ベンチマーク）

```sql
CREATE TABLE market_benchmarks (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,  -- "^GSPC" (S&P500), "^NDX" (NASDAQ100)
    performance_1y DECIMAL(10,4),
    performance_6m DECIMAL(10,4),
    performance_3m DECIMAL(10,4),
    performance_1m DECIMAL(10,4),
    recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_benchmark_per_day
        UNIQUE (symbol, (recorded_at::date))
);

CREATE INDEX idx_market_benchmarks_symbol_date
    ON market_benchmarks(symbol, recorded_at DESC);
```

- 更新頻度: 1日1回（市場終了後）
- 用途: RS計算のベンチマーク
- Job 0 で取得、Job 1 で参照

#### job_executions（ジョブ実行履歴）

```sql
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

CREATE INDEX idx_job_executions_type_created
    ON job_executions(job_type, created_at DESC);
```

---

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ジョブ分離アーキテクチャ                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  【Job 0】ベンチマーク収集ジョブ (CollectBenchmarksJob)        ← 1日1回     │
│    ─────────────────────────────────────────                                │
│    目的: S&P500/NASDAQ100のパフォーマンスを取得し、DBに保存                  │
│    特徴:                                                                    │
│      - 外部API呼び出し（市場指数のみ）                                       │
│      - market_benchmarks テーブルに保存                                     │
│      - 1日1回で十分（市場終了後）                                            │
│    所要時間: 数秒                                                           │
│                                                                             │
│                              ↓ ベンチマーク準備完了                          │
│                                                                             │
│  【Job 1】データ収集ジョブ (CollectStockDataJob)               ← 必要時     │
│    ─────────────────────────────────────────                                │
│    目的: 個別銘柄のデータを取得し、relative_strength を計算                  │
│    特徴:                                                                    │
│      - 各銘柄を独立して処理                                                  │
│      - ベンチマークは **DBから参照**（API呼び出しなし）                       │
│      - rs_rating, canslim_score は計算しない（後続ジョブに委譲）              │
│    所要時間: 数分〜数十分（銘柄数に依存）                                     │
│                                                                             │
│                              ↓ 完了後に自動実行                              │
│                                                                             │
│  【Job 2】RS Rating 再計算ジョブ (RecalculateRSRatingJob)                   │
│    ─────────────────────────────────────────                                │
│    目的: DB内の全銘柄でパーセンタイルランキングを計算                         │
│    特徴:                                                                    │
│      - 外部API呼び出しなし                                                   │
│      - DB内の relative_strength を使用                                      │
│      - 全銘柄の rs_rating を一括更新                                        │
│    所要時間: 数秒                                                           │
│                                                                             │
│                              ↓ 完了後に自動実行                              │
│                                                                             │
│  【Job 3】CAN-SLIMスコア再計算ジョブ (RecalculateCANSLIMScoreJob)            │
│    ─────────────────────────────────────────                                │
│    目的: DB内のデータを元にCAN-SLIMスコアを計算                              │
│    特徴:                                                                    │
│      - 外部API呼び出しなし                                                   │
│      - rs_rating 確定後に実行                                               │
│      - 全銘柄の canslim_score を一括更新                                    │
│    所要時間: 数秒                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## タイムチャート

### 日次更新フロー

```
市場終了後 (16:00 ET / 翌 06:00 JST)
│
▼
┌────────────────────────────────────────────────────────────────────────────┐
│ Job 0: CollectBenchmarks (数秒)                                            │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ 1. S&P500 (^GSPC) の1年パフォーマンス取得                               │ │
│ │ 2. NASDAQ100 (^NDX) の1年パフォーマンス取得                             │ │
│ │ 3. market_benchmarks テーブルに保存                                     │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
│
▼ ベンチマークがDBに保存済み
│
┌────────────────────────────────────────────────────────────────────────────┐
│ Job 1: CollectStockData (数分〜数十分)                                      │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ 1. DBからベンチマーク取得 (S&P500 performance_1y)     ← API呼び出しなし │ │
│ │ 2. 銘柄ループ:                                                         │ │
│ │    ├─ get_quote(symbol)                                                │ │
│ │    ├─ get_financial_metrics(symbol)                                    │ │
│ │    ├─ get_price_history(symbol, 1y)                                    │ │
│ │    ├─ relative_strength = stock_perf / benchmark_perf * 100            │ │
│ │    └─ stocks, stock_prices, stock_metrics に保存                       │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
│
▼
┌────────────────────────────────────────────────────────────────────────────┐
│ Job 2: RecalculateRSRating (数秒)                                          │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ 1. 全銘柄の relative_strength 取得                                      │ │
│ │ 2. パーセンタイル計算 → rs_rating (1-99)                                │ │
│ │ 3. stock_metrics.rs_rating を一括更新                                   │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
│
▼
┌────────────────────────────────────────────────────────────────────────────┐
│ Job 3: RecalculateCANSLIM (数秒)                                           │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ 1. 全銘柄のスコア計算に必要なデータ取得                                  │ │
│ │ 2. CAN-SLIMスコア計算 (0-100)                                           │ │
│ │ 3. stock_metrics.canslim_score を一括更新                               │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
```

### 効率化のポイント

```
旧フロー（非効率）:
┌──────────────────────────────────────────────────────────────────┐
│ Job 1 実行ごとに S&P500 取得                                      │
│                                                                  │
│   Run 1: [S&P500取得] → 銘柄処理...                              │
│   Run 2: [S&P500取得] → 銘柄処理...   ← 無駄なAPI呼び出し        │
│   Run 3: [S&P500取得] → 銘柄処理...   ← 無駄なAPI呼び出し        │
└──────────────────────────────────────────────────────────────────┘

新フロー（効率的）:
┌──────────────────────────────────────────────────────────────────┐
│ Job 0 で1日1回取得、DBにキャッシュ                                │
│                                                                  │
│   Job 0: [S&P500取得] → DB保存 (1日1回)                          │
│   Job 1 Run 1: [DB参照] → 銘柄処理...   ← API呼び出しなし        │
│   Job 1 Run 2: [DB参照] → 銘柄処理...   ← API呼び出しなし        │
│   Job 1 Run 3: [DB参照] → 銘柄処理...   ← API呼び出しなし        │
└──────────────────────────────────────────────────────────────────┘
```

---

## Job 0: ベンチマーク収集ジョブ

### 責務

- 市場指数（S&P500, NASDAQ100）のパフォーマンスを取得
- `market_benchmarks` テーブルに保存

### 入力

```python
@dataclass
class CollectBenchmarksInput:
    indices: list[str] = field(default_factory=lambda: ["^GSPC", "^NDX"])
```

### 処理フロー

```
1. 対象指数ごとにループ
   for index in ["^GSPC", "^NDX"]:
     ├─ get_price_history(index, period="1y")
     ├─ calculate_performance(history, periods=["1y", "6m", "3m", "1m"])
     └─ UPSERT market_benchmarks

2. 完了
```

### 出力

```python
@dataclass
class CollectBenchmarksOutput:
    indices_updated: int
    benchmarks: dict[str, float]  # {"^GSPC": 25.3, "^NDX": 30.1}
```

### 実行タイミング

- **推奨**: 1日1回（米国市場終了後）
- **手動**: 管理者が明示的に実行可能
- Job 1 より先に実行されている必要がある

---

## Job 1: データ収集ジョブ

### 責務

- 個別銘柄のデータを外部APIから取得
- `relative_strength` を計算（**DBのベンチマークを参照**）
- 3テーブルに保存（stocks, stock_prices, stock_metrics）

### 入力

```python
@dataclass
class CollectStockDataInput:
    symbols: list[str]       # 対象銘柄リスト
    source: str              # "sp500" | "nasdaq100" | "custom"
```

### 処理フロー

```
1. ジョブ開始

2. DBからベンチマーク取得（API呼び出しなし）
   └─ SELECT performance_1y FROM market_benchmarks
      WHERE symbol = '^GSPC'
      ORDER BY recorded_at DESC LIMIT 1

3. 銘柄ごとにデータ収集
   for symbol in symbols:
     ├─ get_quote(symbol)
     ├─ get_financial_metrics(symbol)
     ├─ get_price_history(symbol)
     ├─ calculate_relative_strength(stock_perf, benchmark_perf)
     ├─ UPSERT stocks (マスター)
     ├─ INSERT stock_prices (価格スナップショット)
     ├─ INSERT stock_metrics (rs_rating=NULL, canslim_score=NULL)
     └─ 進捗更新

4. ジョブ完了
   └─ 後続ジョブをトリガー (Job 2)
```

### 保存データ

| テーブル | カラム | 値 |
|---------|-------|-----|
| stocks | symbol, name, industry | マスター情報 |
| stock_prices | price, volume, ... | APIから取得した値 |
| stock_metrics | relative_strength | 計算値 (例: 105.2) |
| stock_metrics | rs_rating | NULL (Job 2で計算) |
| stock_metrics | canslim_score | NULL (Job 3で計算) |

### エラーハンドリング

- ベンチマークが存在しない場合: Job 0 の実行を促すエラー
- 銘柄ごとにtry-catch
- 失敗した銘柄はスキップし、エラーリストに記録
- 他銘柄の処理は継続

---

## Job 2: RS Rating 再計算ジョブ

### 責務

- DB内の全銘柄の `relative_strength` を取得
- パーセンタイルランキングを計算
- `stock_metrics.rs_rating` を一括更新

### 入力

なし（DB全体を対象）

### 処理フロー

```
1. DB から全銘柄の relative_strength を取得
   SELECT symbol, relative_strength
   FROM stock_metrics
   WHERE relative_strength IS NOT NULL
     AND calculated_at::date = CURRENT_DATE

2. パーセンタイル計算
   sorted_rs = sorted(all_relative_strengths)
   for symbol, rs in stocks:
     rank = count(sorted_rs <= rs)
     percentile = (rank / total) * 100
     rs_rating = clamp(percentile, 1, 99)

3. 一括更新
   UPDATE stock_metrics SET rs_rating = ?
   WHERE symbol = ? AND calculated_at::date = CURRENT_DATE

4. 後続ジョブをトリガー (Job 3)
```

### パフォーマンス

- 外部API呼び出しなし
- 500銘柄でも数秒で完了

---

## Job 3: CAN-SLIMスコア再計算ジョブ

### 責務

- DB内のデータを元にCAN-SLIMスコアを計算
- `stock_metrics.canslim_score` を一括更新

### 入力

なし（DB全体を対象）

### 処理フロー

```
1. DB から全銘柄のスコア計算に必要なデータを取得
   SELECT
     sm.symbol,
     sm.eps_growth_quarterly,
     sm.eps_growth_annual,
     sp.week_52_high,
     sp.price,
     sp.volume,
     sp.avg_volume_50d,
     sm.rs_rating,
     sm.institutional_ownership
   FROM stock_metrics sm
   JOIN stock_prices sp ON sm.symbol = sp.symbol
     AND sp.recorded_at::date = CURRENT_DATE

2. 各銘柄のCAN-SLIMスコアを計算
   for stock in stocks:
     canslim_score = CANSLIMScore.calculate(...)

3. 一括更新
   UPDATE stock_metrics SET canslim_score = ?
   WHERE symbol = ? AND calculated_at::date = CURRENT_DATE
```

---

## Domain 設計

### 設計方針

**DDD（ドメイン駆動設計）** に従い、以下の原則で責務を分離する：

- **1エンティティ = 1ファイル**
- **entities/ にはEntity, Value Objectのみ配置**
- **DTOはPresentation層（schemas/）に配置**
- **ドメインサービスは既存のものを活用（Phase 4で整理）**

### ディレクトリ構造

```
backend/src/domain/
├── entities/              # Entity / Value Object
│   ├── __init__.py
│   ├── stock_identity.py      # Entity（Aggregate Root）
│   ├── price_snapshot.py      # Value Object
│   ├── stock_metrics.py       # Value Object
│   └── market_benchmark.py    # Value Object
│
└── services/              # ドメインサービス（既存）
    ├── __init__.py
    ├── rs_rating_calculator.py    # RS Rating計算（Job 2で使用）
    ├── eps_growth_calculator.py   # EPS成長率計算（Job 3で使用）
    └── ...

backend/src/presentation/
└── schemas/
    └── screener.py            # StockSummarySchema 等（既存）
```

### 各クラスの責務

#### entities/（Domain層）

| ファイル | クラス | 対応テーブル | DDD分類 |
|----------|--------|-------------|---------|
| stock_identity.py | StockIdentity | stocks | Entity（Aggregate Root） |
| price_snapshot.py | PriceSnapshot | stock_prices | Value Object |
| stock_metrics.py | StockMetrics | stock_metrics | Value Object |
| market_benchmark.py | MarketBenchmark | market_benchmarks | Value Object |

#### schemas/（Presentation層・既存）

| ファイル | クラス | 用途 |
|----------|--------|------|
| screener.py | StockSummarySchema | 一覧表示用DTO |
| screener.py | StockDetailSchema | 詳細表示用DTO |

#### services/（ドメインサービス・既存）

| ファイル | クラス | 責務 | 使用Job |
|----------|--------|------|--------|
| rs_rating_calculator.py | RSRatingCalculator | RS Rating計算 | Job 2 |
| eps_growth_calculator.py | EPSGrowthCalculator | EPS成長率計算 | Job 3 |

### エンティティ定義

#### stock_identity.py

```python
@dataclass(frozen=True)
class StockIdentity:
    """銘柄マスター"""
    symbol: str
    name: str | None = None
    industry: str | None = None
```

#### price_snapshot.py

```python
@dataclass(frozen=True)
class PriceSnapshot:
    """価格スナップショット"""
    symbol: str
    price: float | None
    change_percent: float | None
    volume: int | None
    avg_volume_50d: int | None
    market_cap: int | None
    week_52_high: float | None
    week_52_low: float | None
    recorded_at: datetime
```

#### stock_metrics.py

```python
@dataclass(frozen=True)
class StockMetrics:
    """計算指標"""
    symbol: str
    eps_growth_quarterly: float | None   # C - Current Quarterly Earnings
    eps_growth_annual: float | None      # A - Annual Earnings
    institutional_ownership: float | None # I - Institutional Sponsorship
    relative_strength: float | None      # Job 1: S&P500比の生値
    rs_rating: int | None                # Job 2: パーセンタイル (1-99)
    canslim_score: int | None            # Job 3: 0-100
    calculated_at: datetime
```

#### market_benchmark.py

```python
@dataclass(frozen=True)
class MarketBenchmark:
    """市場ベンチマーク"""
    symbol: str  # "^GSPC", "^NDX"
    performance_1y: float | None
    performance_6m: float | None
    performance_3m: float | None
    performance_1m: float | None
    recorded_at: datetime
```

---

## Repository 設計

### 設計方針

**1テーブル = 1リポジトリ** の原則に従い、責務を明確に分離する。
読み取り専用の集約操作は別途 QueryRepository として切り出す。

### ディレクトリ構造

```
backend/src/domain/repositories/
├── __init__.py
├── stock_identity_repository.py   # stocks テーブル
├── price_snapshot_repository.py   # stock_prices テーブル
├── stock_metrics_repository.py    # stock_metrics テーブル
├── benchmark_repository.py        # market_benchmarks テーブル
└── stock_query_repository.py      # 読み取り専用（JOIN/集約操作）
```

### 各リポジトリの責務

| リポジトリ | テーブル | 責務 |
|-----------|---------|------|
| StockIdentityRepository | stocks | マスターCRUD |
| PriceSnapshotRepository | stock_prices | 価格スナップショット保存・取得 |
| StockMetricsRepository | stock_metrics | 指標保存・Job 2, 3用更新 |
| BenchmarkRepository | market_benchmarks | ベンチマーク保存・取得 |
| StockQueryRepository | JOIN | スクリーニング・集約取得（読み取り専用）→ `StockData` を返す |

### インターフェース定義

#### stock_identity_repository.py

```python
class StockIdentityRepository(ABC):
    """銘柄マスターリポジトリ"""

    @abstractmethod
    async def save(self, identity: StockIdentity) -> None:
        """保存（UPSERT）"""
        pass

    @abstractmethod
    async def get(self, symbol: str) -> StockIdentity | None:
        """取得"""
        pass

    @abstractmethod
    async def get_all_symbols(self) -> list[str]:
        """全シンボル取得"""
        pass

    @abstractmethod
    async def delete(self, symbol: str) -> bool:
        """削除"""
        pass
```

#### price_snapshot_repository.py

```python
class PriceSnapshotRepository(ABC):
    """価格スナップショットリポジトリ"""

    @abstractmethod
    async def save(self, snapshot: PriceSnapshot) -> None:
        """保存"""
        pass

    @abstractmethod
    async def get_latest(self, symbol: str) -> PriceSnapshot | None:
        """最新取得"""
        pass

    @abstractmethod
    async def get_by_date(self, symbol: str, date: date) -> PriceSnapshot | None:
        """日付指定取得"""
        pass
```

#### stock_metrics_repository.py

```python
class StockMetricsRepository(ABC):
    """計算指標リポジトリ"""

    @abstractmethod
    async def save(self, metrics: StockMetrics) -> None:
        """保存"""
        pass

    @abstractmethod
    async def get_latest(self, symbol: str) -> StockMetrics | None:
        """最新取得"""
        pass

    # ----- Job 2用 -----
    @abstractmethod
    async def get_all_with_relative_strength(self) -> list[tuple[str, float]]:
        """relative_strengthを持つ全銘柄を取得"""
        pass

    @abstractmethod
    async def bulk_update_rs_rating(self, updates: list[tuple[str, int]]) -> int:
        """rs_ratingを一括更新"""
        pass

    # ----- Job 3用 -----
    @abstractmethod
    async def bulk_update_canslim_score(self, updates: list[tuple[str, int]]) -> int:
        """canslim_scoreを一括更新"""
        pass
```

#### benchmark_repository.py

```python
class BenchmarkRepository(ABC):
    """市場ベンチマークリポジトリ"""

    @abstractmethod
    async def save(self, benchmark: MarketBenchmark) -> None:
        """保存（UPSERT）"""
        pass

    @abstractmethod
    async def get_latest(self, symbol: str) -> MarketBenchmark | None:
        """最新取得"""
        pass

    @abstractmethod
    async def get_latest_performance_1y(self, symbol: str) -> float | None:
        """1年パフォーマンス取得（Job 1用）"""
        pass
```

#### stock_query_repository.py

```python
@dataclass
class StockData:
    """クエリ結果用のデータクラス（Infrastructure層）"""
    identity: StockIdentity
    price: PriceSnapshot | None
    metrics: StockMetrics | None

class StockQueryRepository(ABC):
    """読み取り専用クエリリポジトリ"""

    @abstractmethod
    async def get_stock(self, symbol: str) -> StockData | None:
        """銘柄を集約して取得（identity + price + metrics）"""
        pass

    @abstractmethod
    async def get_stocks(self, symbols: list[str]) -> list[StockData]:
        """複数銘柄を集約して取得"""
        pass

    @abstractmethod
    async def screen(
        self,
        filter_: ScreenerFilter,
        limit: int = 20,
        offset: int = 0,
    ) -> ScreenerResult:
        """CAN-SLIM条件でスクリーニング"""
        pass

    @abstractmethod
    async def get_all_for_canslim(self) -> list[StockData]:
        """CAN-SLIMスコア計算に必要な全銘柄を取得（Job 3用）"""
        pass
```

**注意**: `StockData` はInfrastructure層のクエリ用データクラス。Application層で `StockSummarySchema` 等のDTOに変換する。

---

## API設計

### 1. ベンチマーク更新

```http
POST /api/admin/benchmarks/refresh
```

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "job_id": "benchmark_20240115_060000",
    "indices_updated": 2,
    "benchmarks": {
      "^GSPC": 25.3,
      "^NDX": 30.1
    }
  }
}
```

### 2. データ収集開始

```http
POST /api/admin/screener/refresh
Content-Type: application/json

{
  "symbols": ["AAPL", "NVDA", "MSFT"],  // または省略
  "source": "sp500"  // "sp500" | "nasdaq100" | "custom"
}
```

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "job_id": "collect_20240115_103000",
    "job_type": "collect_data",
    "status": "started",
    "total_symbols": 500
  }
}
```

### 3. 再計算のみ

```http
POST /api/admin/screener/recalculate
Content-Type: application/json

{
  "target": "rs_rating"  // "rs_rating" | "canslim_score" | "all"
}
```

---

## 実行パターン

### パターン A: フル更新（日次推奨）

```
スケジューラー（または管理者）:

1. Job 0: ベンチマーク収集 - 数秒
   POST /admin/benchmarks/refresh

2. Job 1-3: データ収集フロー
   POST /admin/screener/refresh { source: "sp500" }

   実行順序:
     Job 1: データ収集 (500銘柄) - 数十分
     Job 2: RS Rating 再計算 - 数秒 (自動実行)
     Job 3: CAN-SLIMスコア再計算 - 数秒 (自動実行)
```

### パターン B: 追加銘柄の更新

```
管理者: POST /admin/screener/refresh { symbols: ["AAPL"] }

実行順序:
  Job 1: データ収集 (1銘柄) - 数秒
         └─ ベンチマークはDBから参照（API呼び出しなし）
  Job 2: RS Rating 再計算 (全500銘柄) - 数秒 (自動実行)
  Job 3: CAN-SLIMスコア再計算 (全500銘柄) - 数秒 (自動実行)
```

### パターン C: 再計算のみ

```
管理者: POST /admin/screener/recalculate { target: "all" }

実行順序:
  Job 2: RS Rating 再計算 - 数秒
  Job 3: CAN-SLIMスコア再計算 - 数秒 (自動実行)

※ データ収集なし。DB内の既存データで再計算。
```

---

## ジョブディレクトリ構造

```
backend/src/jobs/
├── lib/                              # 共有ユーティリティ
│   ├── __init__.py
│   ├── base.py                       # ジョブ基底クラス
│   ├── context.py                    # 実行コンテキスト
│   └── errors.py                     # ジョブ固有エラー
│
├── executions/                       # 個別ジョブ実装（単一責務）
│   ├── __init__.py
│   ├── collect_benchmarks.py         # Job 0: ベンチマーク収集
│   ├── collect_stock_data.py         # Job 1: データ収集
│   ├── recalculate_rs_rating.py      # Job 2: RS Rating再計算
│   └── recalculate_canslim.py        # Job 3: CAN-SLIMスコア再計算
│
└── flows/                            # 複数ジョブのオーケストレーション
    ├── __init__.py
    ├── refresh_benchmarks.py         # ベンチマーク更新フロー
    └── refresh_screener.py           # 収集 → RS → CAN-SLIM フロー
```

---

## 実装タスク

### Phase 3: DB正規化 + エンティティ/リポジトリ分離

#### 3-1. DBスキーマ
- [x] `init.sql` を4テーブル構成に変更
  - stocks（マスター）
  - stock_prices（価格スナップショット）
  - stock_metrics（計算指標）
  - market_benchmarks（ベンチマーク）

#### 3-2. Domain 設計（DDD準拠）
- [x] `entities/stock_identity.py` - StockIdentity（Entity）
- [x] `entities/price_snapshot.py` - PriceSnapshot（VO）
- [x] `entities/stock_metrics.py` - StockMetrics（VO）
- [x] `entities/market_benchmark.py` - MarketBenchmark（VO）
- [x] `entities/__init__.py` - エクスポート整理
- 注: DTO（StockSummarySchema等）は既存の `presentation/schemas/screener.py` を使用
- 注: ドメインサービスは既存の `RSRatingCalculator`, `EPSGrowthCalculator` を Phase 4 で活用

#### 3-3. Repository インターフェース（1テーブル = 1リポジトリ）
- [x] `stock_identity_repository.py` - stocks テーブル
- [x] `price_snapshot_repository.py` - stock_prices テーブル
- [x] `stock_metrics_repository.py` - stock_metrics テーブル
- [x] `benchmark_repository.py` - market_benchmarks テーブル
- [x] `stock_query_repository.py` - 読み取り専用（JOIN/集約）
- [x] `__init__.py` - エクスポート整理
- 注: 既存の `stock_repository.py` は 3-4 で移行後に削除

#### 3-4. Infrastructure 実装
- [x] SQLAlchemy モデル作成（4テーブル分）
  - StockModel, StockPriceModel, StockMetricsModel, MarketBenchmarkModel
- [x] Repository 実装（5リポジトリ）
  - PostgresStockIdentityRepository
  - PostgresPriceSnapshotRepository
  - PostgresStockMetricsRepository
  - PostgresBenchmarkRepository
  - PostgresStockQueryRepository
- 注: Mapperはリポジトリ内で変換（シンプルなため別クラス不要）
- 注: 旧リポジトリ（PostgresStockRepository）は互換性のため残存

#### 3-5. Job 0, 1 実装
- [ ] Job 0: `CollectBenchmarksJob` 実装
- [ ] Job 1: ベンチマークをDBから参照するよう修正

### Phase 4: Job 2, 3 実装

- [ ] Job 2: `RecalculateRSRatingJob` 実装
- [ ] Job 3: `RecalculateCANSLIMJob` 実装
- [ ] Flow を4ジョブ構成に更新

### Phase 5: API・フロントエンド更新

- [ ] `/admin/benchmarks/refresh` エンドポイント追加
- [ ] `/admin/screener/recalculate` エンドポイント追加
- [ ] フロントエンドの進捗表示更新

---

## 備考

- Job 0 は1日1回で十分（市場指数は終値確定後に変わらない）
- Job 1 は複数回実行可能（ベンチマークはDBキャッシュ）
- 正規化によりデータ履歴の保持が容易に
- 将来的に stock_prices, stock_metrics の履歴を活用可能
