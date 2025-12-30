# Domain層 実装ガイド

## 概要

Domain層はクリーンアーキテクチャの最内層であり、ビジネスルールとドメインロジックを定義する。
フレームワークや外部ライブラリに依存しない純粋なPythonコードで構成される。

---

## ディレクトリ構造

```
backend/src/domain/
├── models/                # Entity / Value Object（ドメインモデル）
│   ├── __init__.py
│   ├── stock_identity.py      # Entity（Aggregate Root）
│   ├── price_snapshot.py      # Value Object
│   ├── stock_metrics.py       # Value Object
│   ├── market_benchmark.py    # Value Object
│   ├── market_status.py       # Entity
│   ├── quote.py               # Value Object
│   ├── watchlist_item.py      # Entity
│   ├── paper_trade.py         # Entity
│   └── canslim_config.py      # Value Object（スコア計算設定）
│
├── constants/             # ドメイン固有の定数
│   ├── __init__.py
│   ├── trading_days.py        # 営業日数定数
│   └── canslim_defaults.py    # スクリーニングデフォルト値
│
├── repositories/          # リポジトリインターフェース
│   ├── __init__.py
│   ├── stock_identity_repository.py
│   ├── price_snapshot_repository.py
│   ├── stock_metrics_repository.py
│   ├── benchmark_repository.py
│   └── stock_query_repository.py
│
├── services/              # ドメインサービス
│   ├── __init__.py
│   ├── relative_strength_calculator.py  # RS計算（IBD式）
│   ├── canslim_score_calculator.py      # CAN-SLIMスコア計算
│   ├── eps_growth_calculator.py
│   ├── performance_calculator.py
│   └── market_analyzer.py
│
└── entities/              # [非推奨] 後方互換用re-export
    └── __init__.py            # models/, constants/ からre-export
```

---

## 構成要素

| 要素 | 責務 | 配置場所 |
|------|------|----------|
| Entity | ビジネスエンティティ、識別子を持つ | `domain/models/` |
| Value Object | 不変の値オブジェクト | `domain/models/` |
| 定数クラス | ドメイン固有の定数定義 | `domain/constants/` |
| Domain Service | 複数エンティティにまたがるロジック | `domain/services/` |
| Repository Interface | データアクセスの抽象インターフェース | `domain/repositories/` |

---

## Models（Entity / Value Object）

### 設計方針

- **1エンティティ = 1ファイル**
- **1テーブル = 1 Entity/VO** でマッピング
- Value Object は `frozen=True` で不変に
- DTOは Presentation層（`schemas/`）に配置

### モデル一覧

| ファイル | クラス | 対応テーブル | DDD分類 |
|----------|--------|-------------|---------|
| stock_identity.py | StockIdentity | stocks | Entity（Aggregate Root） |
| price_snapshot.py | PriceSnapshot | stock_prices | Value Object |
| stock_metrics.py | StockMetrics | stock_metrics | Value Object |
| market_benchmark.py | MarketBenchmark | market_benchmarks | Value Object |
| market_status.py | MarketStatus | - | Entity |
| quote.py | Quote, HistoricalPrice | - | Value Object |
| watchlist_item.py | WatchlistItem | watchlist_items | Entity |
| paper_trade.py | PaperTrade | paper_trades | Entity |
| canslim_config.py | CANSLIMWeights, CANSLIMScoreThresholds | - | Value Object |

---

## Constants（定数クラス）

### 設計方針

- 将来変わることがない固定値を定義
- インスタンス化しない（クラス変数のみ）
- Value Objectとの違い: コンストラクタで値を変更できない

### 定数一覧

| ファイル | クラス | 用途 |
|----------|--------|------|
| trading_days.py | TradingDays | 営業日数（YEAR=252, MONTH_3=63 等） |
| canslim_defaults.py | CANSLIMDefaults | スクリーニングのデフォルト閾値 |

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
- 設定値はValue Objectとしてコンストラクタで注入

### サービス一覧

| サービス | 責務 | 使用箇所 |
|----------|------|---------|
| RelativeStrengthCalculator | IBD式相対強度・RS Rating計算 | Job 0, Job 2 |
| CANSLIMScoreCalculator | CAN-SLIMスコア計算（C/A/N/S/L/I） | Job 3 |
| EPSGrowthCalculator | EPS成長率計算 | Job 1 |
| PerformanceCalculator | パフォーマンス計算 | 各種分析 |
| MarketAnalyzer | マーケット状態判定 | MarketStatus生成 |

---

## 設計原則

1. **外部依存なし**: フレームワーク、DB、APIに依存しない
2. **純粋なロジック**: ビジネスルールのみを表現
3. **テスタビリティ**: モックなしで単体テスト可能
4. **不変性優先**: Value Objectは`frozen=True`で不変に
