# スクリーニングデータ更新 設計書

## 概要

スクリーニングデータを更新するためのジョブ設計。
責務を明確に分離し、各ジョブが独立して実行可能な設計とする。

---

## 設計原則

1. **責務分離**: 1ジョブ = 1責務
2. **独立性**: 各銘柄の処理が他銘柄に影響しない
3. **再実行性**: 失敗時に該当ジョブのみ再実行可能
4. **段階的計算**: Job 1 → Job 2 → Job 3 の順に段階的にフィールドを更新
5. **フラット構造**: 単一テーブル（canslim_stocks）で全データを管理

---

## DBスキーマ

### 設計方針

**フラットテーブル設計**を採用。CANSLIMStock 集約を1テーブルで表現する。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            テーブル構成                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  canslim_stocks (CAN-SLIM分析銘柄)                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ symbol (PK)              -- ティッカーシンボル                        │   │
│  │ date (PK)                -- 記録日                                   │   │
│  │                                                                      │   │
│  │ -- 銘柄情報                                                          │   │
│  │ name, industry                                                       │   │
│  │                                                                      │   │
│  │ -- 価格データ（Job 1 で更新）                                         │   │
│  │ price, change_percent, volume, avg_volume_50d                        │   │
│  │ market_cap, week_52_high, week_52_low                                │   │
│  │                                                                      │   │
│  │ -- 財務データ（Job 1 で更新）                                         │   │
│  │ eps_growth_quarterly, eps_growth_annual, institutional_ownership     │   │
│  │                                                                      │   │
│  │ -- 相対強度（Job 1 で更新）                                           │   │
│  │ relative_strength                                                    │   │
│  │                                                                      │   │
│  │ -- RS Rating（Job 2 で更新）                                          │   │
│  │ rs_rating                                                            │   │
│  │                                                                      │   │
│  │ -- CAN-SLIMスコア（Job 3 で更新）                                     │   │
│  │ canslim_score, score_c, score_a, score_n, score_s, score_l, score_i  │   │
│  │                                                                      │   │
│  │ -- メタデータ                                                        │   │
│  │ updated_at                                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  market_snapshots (市場状態)                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ vix, sp500_price, sp500_rsi, sp500_ma200, put_call_ratio            │   │
│  │ condition, score, recorded_at                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  refresh_jobs (ジョブ進捗管理)                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ job_id, status, source, total_symbols, processed_count              │   │
│  │ succeeded_count, failed_count, errors, started_at, completed_at     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### テーブル定義

#### canslim_stocks（CAN-SLIM分析銘柄）

```sql
CREATE TABLE canslim_stocks (
    -- 主キー（複合）
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,

    -- 銘柄情報
    name VARCHAR(100),
    industry VARCHAR(50),

    -- 価格データ（Job 1 で更新）
    price DECIMAL(10,2),
    change_percent DECIMAL(5,2),
    volume BIGINT,
    avg_volume_50d BIGINT,
    market_cap BIGINT,
    week_52_high DECIMAL(10,2),
    week_52_low DECIMAL(10,2),

    -- 財務データ（Job 1 で更新）
    eps_growth_quarterly DECIMAL(10,2),
    eps_growth_annual DECIMAL(10,2),
    institutional_ownership DECIMAL(5,2),

    -- RS関連
    relative_strength DECIMAL(10,4),  -- Job 1: S&P500比の生値
    rs_rating INTEGER,                 -- Job 2: パーセンタイル (1-99)

    -- CAN-SLIMスコア（Job 3 で更新）
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
```

- 更新頻度: Job実行時
- 用途: CAN-SLIM分析の全データを1レコードで管理
- 履歴保持: 日付ごとにレコードを保持

---

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ジョブ分離アーキテクチャ                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  【Job 1】データ収集ジョブ (CollectStockDataJob)                ← 必要時     │
│    ─────────────────────────────────────────                                │
│    目的: 個別銘柄のデータを取得し、relative_strength を計算                  │
│    更新フィールド:                                                          │
│      - price, change_percent, volume, avg_volume_50d, market_cap           │
│      - week_52_high, week_52_low                                           │
│      - eps_growth_quarterly, eps_growth_annual, institutional_ownership    │
│      - relative_strength                                                   │
│    所要時間: 数分〜数十分（銘柄数に依存）                                     │
│                                                                             │
│                              ↓ 完了後に自動実行                              │
│                                                                             │
│  【Job 2】RS Rating 計算ジョブ (CalculateRSRatingJob)                       │
│    ─────────────────────────────────────────                                │
│    目的: DB内の全銘柄でパーセンタイルランキングを計算                         │
│    更新フィールド:                                                          │
│      - rs_rating (1-99)                                                    │
│    特徴:                                                                    │
│      - 外部API呼び出しなし                                                   │
│      - DB内の relative_strength を使用                                      │
│    所要時間: 数秒                                                           │
│                                                                             │
│                              ↓ 完了後に自動実行                              │
│                                                                             │
│  【Job 3】CAN-SLIMスコア計算ジョブ (CalculateCANSLIMJob)                     │
│    ─────────────────────────────────────────                                │
│    目的: DB内のデータを元にCAN-SLIMスコアを計算                              │
│    更新フィールド:                                                          │
│      - canslim_score (0-100)                                               │
│      - score_c, score_a, score_n, score_s, score_l, score_i, score_m       │
│    特徴:                                                                    │
│      - 外部API呼び出しなし                                                   │
│      - rs_rating 確定後に実行                                               │
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
│ Job 1: CollectStockData (数分〜数十分)                                      │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ 1. 銘柄ループ:                                                         │ │
│ │    ├─ get_quote(symbol)                                                │ │
│ │    ├─ get_financial_metrics(symbol)                                    │ │
│ │    ├─ get_price_history(symbol, 1y)                                    │ │
│ │    ├─ relative_strength = RSCalculator.calculate(...)                  │ │
│ │    └─ canslim_stocks に UPSERT（rs_rating, canslim_score は NULL）     │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
│
▼
┌────────────────────────────────────────────────────────────────────────────┐
│ Job 2: CalculateRSRating (数秒)                                            │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ 1. 全銘柄の relative_strength 取得                                      │ │
│ │ 2. パーセンタイル計算 → rs_rating (1-99)                                │ │
│ │ 3. canslim_stocks.rs_rating を一括更新                                  │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
│
▼
┌────────────────────────────────────────────────────────────────────────────┐
│ Job 3: CalculateCANSLIM (数秒)                                             │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ 1. 全銘柄のスコア計算に必要なデータ取得                                  │ │
│ │ 2. CAN-SLIMスコア計算 (0-100)                                           │ │
│ │ 3. canslim_stocks.canslim_score を一括更新                              │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Domain 設計

### 設計方針

**DDD（ドメイン駆動設計）** に従い、フラット構造の集約で設計:

- **1集約 = 1テーブル**: CANSLIMStock 集約が canslim_stocks テーブルに対応
- **段階的計算対応**: NULL許容フィールドで Job 1→2→3 の段階的更新に対応
- **ドメインロジック集約**: スクリーニング判定、計算完了チェック等を集約内に実装

### ディレクトリ構造

```
backend/src/domain/
├── models/
│   ├── __init__.py
│   ├── canslim_stock.py          # CANSLIMStock 集約ルート
│   └── screening_criteria.py     # スクリーニング条件（値オブジェクト）
│
├── repositories/
│   ├── __init__.py
│   └── canslim_stock_repository.py  # リポジトリインターフェース
│
└── services/
    ├── __init__.py
    ├── rs_calculator.py           # RS Rating計算
    └── canslim_score_calculator.py # CAN-SLIMスコア計算
```

### CANSLIMStock 集約

```python
@dataclass
class CANSLIMStock:
    """CAN-SLIM分析銘柄（集約ルート・フラット構造）

    計算フェーズと更新順序:
        Job 1: 価格データ取得
            → price, change_percent, volume, avg_volume_50d, market_cap,
              week_52_high, week_52_low, eps_growth_quarterly, eps_growth_annual,
              institutional_ownership, relative_strength

        Job 2: RS Rating 計算（全銘柄の relative_strength が必要）
            → rs_rating

        Job 3: CAN-SLIM スコア計算（rs_rating が必要）
            → canslim_score, score_c, score_a, score_n, score_s, score_l, score_i, score_m
    """

    # === 識別子（必須） ===
    symbol: str
    date: date

    # === 銘柄情報 ===
    name: str | None = None
    industry: str | None = None

    # === 価格データ（Job 1 で更新） ===
    price: Decimal | None = None
    change_percent: Decimal | None = None
    volume: int | None = None
    avg_volume_50d: int | None = None
    market_cap: int | None = None
    week_52_high: Decimal | None = None
    week_52_low: Decimal | None = None

    # === 財務データ（Job 1 で更新） ===
    eps_growth_quarterly: Decimal | None = None
    eps_growth_annual: Decimal | None = None
    institutional_ownership: Decimal | None = None

    # === 相対強度（Job 1 で更新） ===
    relative_strength: Decimal | None = None

    # === RS Rating（Job 2 で更新） ===
    rs_rating: int | None = None

    # === CAN-SLIM スコア（Job 3 で更新） ===
    canslim_score: int | None = None
    score_c: int | None = None
    score_a: int | None = None
    score_n: int | None = None
    score_s: int | None = None
    score_l: int | None = None
    score_i: int | None = None
    score_m: int | None = None

    # === メタデータ ===
    updated_at: datetime | None = None
```

---

## Repository 設計

### 設計方針

**1集約 = 1リポジトリ** の原則に従い、CANSLIMStockRepository で全操作を提供。
段階的更新に対応するため、部分更新メソッドを用意。

### インターフェース定義

```python
class CANSLIMStockRepository(ABC):
    """CAN-SLIM銘柄リポジトリ

    設計方針:
    - 段階的更新対応: Job 1 → Job 2 → Job 3 の各フェーズで部分更新が可能
    - 一括操作優先: パフォーマンスのため、一括取得・一括更新メソッドを提供
    - UPSERT: 存在すれば更新、なければ挿入
    """

    # === 取得系 ===

    @abstractmethod
    def find_by_symbol_and_date(self, symbol: str, target_date: date) -> CANSLIMStock | None:
        """シンボルと日付で取得"""
        pass

    @abstractmethod
    def find_all_by_date(self, target_date: date) -> list[CANSLIMStock]:
        """指定日の全銘柄を取得"""
        pass

    @abstractmethod
    def find_by_criteria(
        self, target_date: date, criteria: ScreeningCriteria, limit: int, offset: int
    ) -> list[CANSLIMStock]:
        """条件でスクリーニング（計算完了銘柄のみ）"""
        pass

    @abstractmethod
    def find_all_with_relative_strength(self, target_date: date) -> list[CANSLIMStock]:
        """relative_strength が計算済みの全銘柄を取得（Job 2 用）"""
        pass

    # === 保存系 ===

    @abstractmethod
    def save(self, stock: CANSLIMStock) -> None:
        """保存（UPSERT）"""
        pass

    @abstractmethod
    def save_all(self, stocks: list[CANSLIMStock]) -> None:
        """一括保存"""
        pass

    # === 部分更新系（段階的計算用） ===

    @abstractmethod
    def update_rs_ratings(self, target_date: date, rs_ratings: dict[str, int]) -> None:
        """RS Rating を一括更新（Job 2 用）"""
        pass

    @abstractmethod
    def update_canslim_scores(self, target_date: date, scores: dict[str, dict]) -> None:
        """CAN-SLIM スコアを一括更新（Job 3 用）"""
        pass
```

---

## Job 1: データ収集ジョブ

### 責務

- 個別銘柄のデータを外部APIから取得
- `relative_strength` を計算
- `canslim_stocks` テーブルに保存（UPSERT）

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

2. 銘柄ごとにデータ収集
   for symbol in symbols:
     ├─ get_quote(symbol)
     ├─ get_financial_metrics(symbol)
     ├─ get_price_history(symbol)
     ├─ calculate_relative_strength(stock_bars, benchmark_bars)
     ├─ CANSLIMStock を構築（rs_rating=NULL, canslim_score=NULL）
     ├─ repository.save(stock)
     └─ 進捗更新

3. ジョブ完了
   └─ 後続ジョブをトリガー (Job 2)
```

### 保存データ

| フィールド | 値 |
|----------|-----|
| symbol, date | 識別子 |
| price, volume, ... | APIから取得した値 |
| relative_strength | 計算値 (例: 105.2) |
| rs_rating | NULL (Job 2で計算) |
| canslim_score | NULL (Job 3で計算) |

### エラーハンドリング

- 銘柄ごとにtry-catch
- 失敗した銘柄はスキップし、エラーリストに記録
- 他銘柄の処理は継続

---

## Job 2: RS Rating 再計算ジョブ

### 責務

- DB内の全銘柄の `relative_strength` を取得
- パーセンタイルランキングを計算
- `canslim_stocks.rs_rating` を一括更新

### 入力

なし（DB全体を対象）

### 処理フロー

```
1. DB から全銘柄の relative_strength を取得
   repository.find_all_with_relative_strength(target_date)

2. パーセンタイル計算
   sorted_rs = sorted(all_relative_strengths)
   for stock in stocks:
     rank = count(sorted_rs <= stock.relative_strength)
     percentile = (rank / total) * 100
     rs_rating = clamp(percentile, 1, 99)

3. 一括更新
   repository.update_rs_ratings(target_date, {symbol: rs_rating, ...})

4. 後続ジョブをトリガー (Job 3)
```

### パフォーマンス

- 外部API呼び出しなし
- 500銘柄でも数秒で完了

---

## Job 3: CAN-SLIMスコア再計算ジョブ

### 責務

- DB内のデータを元にCAN-SLIMスコアを計算
- `canslim_stocks.canslim_score` を一括更新

### 入力

なし（DB全体を対象）

### 処理フロー

```
1. DB から全銘柄のスコア計算に必要なデータを取得
   stocks = repository.find_all_by_date(target_date)
   ※ rs_rating が設定済みの銘柄のみ

2. 各銘柄のCAN-SLIMスコアを計算
   for stock in stocks:
     canslim_score = CANSLIMScoreCalculator.calculate(stock)

3. 一括更新
   repository.update_canslim_scores(target_date, {symbol: {canslim_score, score_c, ...}, ...})
```

---

## API設計

### 1. データ更新開始

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
    "job_id": "refresh_20240115_103000",
    "status": "started",
    "total_symbols": 500,
    "started_at": "2024-01-15T10:30:00Z"
  }
}
```

### 2. 進捗確認

```http
GET /api/admin/screener/refresh/{job_id}/status
```

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "job_id": "refresh_20240115_103000",
    "status": "running",
    "progress": {
      "total": 500,
      "processed": 225,
      "succeeded": 220,
      "failed": 5,
      "percentage": 45.0
    },
    "timing": {
      "started_at": "2024-01-15T10:30:00Z",
      "elapsed_seconds": 120,
      "estimated_remaining_seconds": 150
    },
    "errors": [
      {"symbol": "XYZ", "error": "Invalid symbol"}
    ]
  }
}
```

### 3. 更新キャンセル

```http
DELETE /api/admin/screener/refresh/{job_id}
```

---

## 実行パターン

### パターン A: フル更新（日次推奨）

```
POST /admin/screener/refresh { source: "sp500" }

実行順序:
  Job 1: データ収集 (500銘柄) - 数十分
  Job 2: RS Rating 再計算 - 数秒 (自動実行)
  Job 3: CAN-SLIMスコア再計算 - 数秒 (自動実行)
```

### パターン B: 追加銘柄の更新

```
POST /admin/screener/refresh { symbols: ["AAPL"] }

実行順序:
  Job 1: データ収集 (1銘柄) - 数秒
  Job 2: RS Rating 再計算 (全銘柄) - 数秒 (自動実行)
  Job 3: CAN-SLIMスコア再計算 (全銘柄) - 数秒 (自動実行)
```

---

## ジョブディレクトリ構造

```
backend/src/
├── application/
│   └── use_cases/
│       └── admin/
│           └── refresh_screener_data.py  # RefreshScreenerDataUseCase
│
├── domain/
│   ├── models/
│   │   ├── canslim_stock.py              # CANSLIMStock 集約
│   │   └── screening_criteria.py
│   ├── repositories/
│   │   └── canslim_stock_repository.py   # リポジトリインターフェース
│   └── services/
│       ├── rs_calculator.py
│       └── canslim_score_calculator.py
│
├── infrastructure/
│   └── repositories/
│       ├── postgres_canslim_stock_repository.py
│       └── postgres_refresh_job_repository.py
│
└── presentation/
    └── api/
        └── admin_controller.py           # API エンドポイント
```

---

## 実装タスク

### 完了済み

- [x] DBスキーマ（canslim_stocks 単一テーブル）
- [x] CANSLIMStock 集約（domain/models/canslim_stock.py）
- [x] ScreeningCriteria 値オブジェクト
- [x] CANSLIMStockRepository インターフェース
- [x] RefreshScreenerDataUseCase（Job 1 相当の処理）
- [x] RefreshJobRepository（進捗管理）
- [x] admin_controller（POST /refresh）
- [x] Frontend 管理画面（/admin/screener）

### 未実装

- [x] admin_controller に GET /status, DELETE 追加
- [ ] Job 2: RS Rating 一括計算の統合
- [ ] Job 3: CAN-SLIM スコア一括計算の統合
- [ ] Frontend 進捗表示（ポーリング）

### 要修正: jobs/executions/ のリファクタリング

ドメイン層リファクタリングにより、`jobs/executions/` 配下のファイルが壊れている。
以下のファイルを新しいドメインモデル（CANSLIMStock, CANSLIMStockRepository）に合わせて修正が必要。

#### 対象ファイル

| ファイル | 状態 | 修正方針 |
|---------|------|---------|
| `collect_stock_data.py` | **修正済み** | CANSLIMStock, CANSLIMStockRepository に変更 |
| `calculate_rs_rating.py` | **修正済み** | CANSLIMStockRepository.update_rs_ratings() に変更 |
| `calculate_canslim.py` | 未修正 | CANSLIMStockRepository.update_canslim_scores() に変更 |
| `collect_benchmarks.py` | 未使用 | 削除または統合（Job 1内でS&P500履歴を取得する設計に変更済み） |

#### 修正方針

**1. collect_stock_data.py (Job 1)**

```python
# Before（壊れている）
from src.domain.models import PriceSnapshot, StockIdentity, StockMetrics
from src.domain.repositories import (
    BenchmarkRepository,
    PriceSnapshotRepository,
    StockIdentityRepository,
    StockMetricsRepository,
)

# After
from src.domain.models.canslim_stock import CANSLIMStock
from src.domain.repositories.canslim_stock_repository import CANSLIMStockRepository
```

**2. calculate_rs_rating.py (Job 2)**

```python
# Before（壊れている）
from src.domain.repositories import StockMetricsRepository

# After
from src.domain.repositories.canslim_stock_repository import CANSLIMStockRepository

# 使用メソッド:
# - find_all_with_relative_strength(target_date)
# - update_rs_ratings(target_date, {symbol: rs_rating})
```

**3. calculate_canslim.py (Job 3)**

```python
# Before（壊れている）
from src.domain.repositories import StockMetricsRepository, StockQueryRepository

# After
from src.domain.repositories.canslim_stock_repository import CANSLIMStockRepository

# 使用メソッド:
# - find_all_by_date(target_date)  ※ rs_rating が設定済みのもの
# - update_canslim_scores(target_date, {symbol: {canslim_score, score_c, ...}})
```

**4. collect_benchmarks.py (Job 0)**

現在の設計では Job 1 内で S&P500 履歴を直接取得しているため、このジョブは不要。
削除するか、将来の拡張用に残す場合は別途検討。

#### 優先度

1. **High**: collect_stock_data.py - Job 1 が動かないと全体が動かない
2. **Medium**: calculate_rs_rating.py, calculate_canslim.py - Job 2, 3 の統合
3. **Low**: collect_benchmarks.py - 現在の設計では不要

---

## 備考

- Job 1 は複数回実行可能
- Job 2, 3 は外部API呼び出しなしで高速実行
- 将来的に canslim_stocks の履歴を活用可能（日付ごとにレコード保持）
