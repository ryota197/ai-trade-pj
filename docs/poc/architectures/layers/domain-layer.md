# Domain層 実装ガイド

## 概要

Domain層はクリーンアーキテクチャの最内層であり、ビジネスルールとドメインロジックを定義する。
フレームワークや外部ライブラリに依存しない純粋なPythonコードで構成される。

---

## ディレクトリ構造

```
backend/src/domain/
├── entities/              # Entity / Value Object
│   ├── __init__.py
│   ├── stock_identity.py      # Entity（Aggregate Root）
│   ├── price_snapshot.py      # Value Object
│   ├── stock_metrics.py       # Value Object
│   ├── market_benchmark.py    # Value Object
│   ├── market_status.py       # Entity
│   └── quote.py               # Value Object
│
├── repositories/          # リポジトリインターフェース
│   ├── __init__.py
│   ├── stock_identity_repository.py
│   ├── price_snapshot_repository.py
│   ├── stock_metrics_repository.py
│   ├── benchmark_repository.py
│   └── stock_query_repository.py
│
└── services/              # ドメインサービス
    ├── __init__.py
    ├── rs_rating_calculator.py
    ├── eps_growth_calculator.py
    └── market_analyzer.py
```

---

## 構成要素

| 要素 | 責務 | 配置場所 |
|------|------|----------|
| Entity | ビジネスエンティティ、識別子を持つ | `domain/entities/` |
| Value Object | 不変の値オブジェクト | `domain/entities/` |
| Domain Service | 複数エンティティにまたがるロジック | `domain/services/` |
| Repository Interface | データアクセスの抽象インターフェース | `domain/repositories/` |

---

## Entities / Value Objects

### 設計方針

- **1エンティティ = 1ファイル**
- **1テーブル = 1 Entity/VO** でマッピング
- Value Object は `frozen=True` で不変に
- DTOは Presentation層（`schemas/`）に配置

### 現在のエンティティ

| ファイル | クラス | 対応テーブル | DDD分類 |
|----------|--------|-------------|---------|
| stock_identity.py | StockIdentity | stocks | Entity（Aggregate Root） |
| price_snapshot.py | PriceSnapshot | stock_prices | Value Object |
| stock_metrics.py | StockMetrics | stock_metrics | Value Object |
| market_benchmark.py | MarketBenchmark | market_benchmarks | Value Object |
| market_status.py | MarketStatus | - | Entity |
| quote.py | Quote, HistoricalPrice | - | Value Object |

---

## Repositories

### 設計方針

- **1テーブル = 1リポジトリ**
- 読み取り専用の集約操作は別途 QueryRepository として切り出す
- インターフェースのみ定義（実装は Infrastructure層）

### リポジトリ一覧

| リポジトリ | テーブル | 責務 |
|-----------|---------|------|
| StockIdentityRepository | stocks | マスターCRUD |
| PriceSnapshotRepository | stock_prices | 価格スナップショット保存・取得 |
| StockMetricsRepository | stock_metrics | 指標保存・Job用更新 |
| BenchmarkRepository | market_benchmarks | ベンチマーク保存・取得 |
| StockQueryRepository | JOIN | スクリーニング・集約取得（読み取り専用） |

---

## Domain Services

### 設計方針

- 複数エンティティにまたがるビジネスロジックを実装
- 外部依存なし（純粋な計算ロジック）

### サービス一覧

| サービス | 責務 | 使用箇所 |
|----------|------|---------|
| RSRatingCalculator | RS Rating計算 | Job 2 |
| EPSGrowthCalculator | EPS成長率計算 | Job 3 |
| MarketAnalyzer | マーケット状態判定 | MarketStatus生成 |

---

## 設計原則

1. **外部依存なし**: フレームワーク、DB、APIに依存しない
2. **純粋なロジック**: ビジネスルールのみを表現
3. **テスタビリティ**: モックなしで単体テスト可能
4. **不変性優先**: Value Objectは`frozen=True`で不変に
