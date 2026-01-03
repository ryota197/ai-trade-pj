# バックエンド レイヤー設計概要

## 概要

クリーンアーキテクチャに基づく4層 + ジョブ層の構成。
依存関係は外側から内側への一方向のみ許可。

---

## アーキテクチャ全体像

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                         外部システム                                     │
│                   (HTTP Client, Database, 外部API)                      │
│                                                                         │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────────┐
│                                                                         │
│                      Presentation Layer                                 │
│                     (FastAPI Controllers)                               │
│                                                                         │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│   │ MarketController│  │ScreenerController│ │ AdminController │        │
│   └────────┬────────┘  └────────┬────────┘  └────────┬────────┘        │
│            │                    │                    │                  │
└────────────┼────────────────────┼────────────────────┼──────────────────┘
             │                    │                    │
┌────────────▼────────────────────▼────────────────────▼──────────────────┐
│                                                                         │
│                      Application Layer                                  │
│                        (Use Cases)                                      │
│                                                                         │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│   │GetMarketStatus  │  │ScreenStocks     │  │RefreshScreener  │        │
│   │UseCase          │  │UseCase          │  │UseCase          │        │
│   └────────┬────────┘  └────────┬────────┘  └────────┬────────┘        │
│            │                    │                    │                  │
└────────────┼────────────────────┼────────────────────┼──────────────────┘
             │                    │                    │
             │                    │                    ▼
             │                    │          ┌─────────────────────────┐
             │                    │          │      Jobs Layer         │
             │                    │          │  ┌─────────────────┐    │
             │                    │          │  │     flows/      │    │
             │                    │          │  │  (オーケストレーション)│
             │                    │          │  └────────┬────────┘    │
             │                    │          │           │             │
             │                    │          │  ┌────────▼────────┐    │
             │                    │          │  │   executions/   │    │
             │                    │          │  │  (個別ジョブ実行) │    │
             │                    │          │  └────────┬────────┘    │
             │                    │          │           │             │
             │                    │          │  ┌────────▼────────┐    │
             │                    │          │  │      lib/       │    │
             │                    │          │  │  (共通基盤)      │    │
             │                    │          │  └─────────────────┘    │
             │                    │          └─────────────────────────┘
             │                    │                    │
┌────────────▼────────────────────▼────────────────────▼──────────────────┐
│                                                                         │
│                       Domain Layer                                      │
│                  (Entities, Value Objects, Services)                    │
│                                                                         │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│   │     Stock       │  │  CANSLIMScore   │  │ MarketCondition │        │
│   │    (Entity)     │  │ (Value Object)  │  │   (Service)     │        │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                                │ Interface (Repository, Gateway)
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                     Infrastructure Layer                                │
│               (Repository実装, 外部サービス連携)                          │
│                                                                         │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│   │StockRepository  │  │MarketDataGateway│  │  Database       │        │
│   │(SQLAlchemy実装) │  │(yfinance実装)   │  │  (PostgreSQL)   │        │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 依存関係ルール

```
Presentation  →  Application  →  Domain  ←  Infrastructure
                      ↓
                    Jobs
```

| From | To | 許可 | 説明 |
|------|-----|-----|------|
| Presentation | Application | ○ | UseCaseを呼び出す |
| Presentation | Domain | ○ | DTOへの変換で参照 |
| Presentation | Infrastructure | × | 直接アクセス禁止 |
| Application | Domain | ○ | Entity/Service を使用 |
| Application | Infrastructure | × | Interface経由のみ |
| Application | Jobs | ○ | Flowをトリガー |
| Jobs | Domain | ○ | Entity/Service を使用 |
| Jobs | Infrastructure | × | Interface経由のみ |
| Infrastructure | Domain | ○ | Interface を実装 |
| Domain | 他層 | × | 依存なし（最内層） |

---

## 各層の責務

### 1. Domain Layer（最内層）

**場所**: `backend/src/domain/`

**責務**: ビジネスルールとビジネスロジックの定義

**含まれるもの**:
- **Entities**: ビジネスの中核概念（Stock, Trade, Watchlist）
- **Value Objects**: 不変の値（CANSLIMScore, RSRating, MarketCondition）
- **Domain Services**: 複数Entityにまたがるロジック
- **Repository Interfaces**: データアクセスの抽象化

```
domain/
├── entities/
│   ├── stock.py              # 銘柄エンティティ
│   ├── trade.py              # 取引エンティティ
│   └── watchlist.py          # ウォッチリストエンティティ
├── value_objects/
│   ├── canslim_score.py      # CAN-SLIMスコア
│   ├── rs_rating.py          # RS Rating
│   └── market_condition.py   # マーケット状態
├── services/
│   ├── canslim_calculator.py # CAN-SLIM計算ロジック
│   └── market_analyzer.py    # マーケット分析ロジック
└── repositories/
    ├── stock_repository.py   # Interface
    └── trade_repository.py   # Interface
```

**原則**:
- 外部依存なし（純粋なPythonのみ）
- フレームワーク非依存
- テストが容易

---

### 2. Application Layer

**場所**: `backend/src/application/`

**責務**: ユースケースの実装、ワークフローの調整

**含まれるもの**:
- **Use Cases**: アプリケーション固有のビジネスルール
- **DTOs**: 層間のデータ転送オブジェクト
- **Application Services**: ユースケース間で共有するロジック

```
application/
├── use_cases/
│   ├── market/
│   │   └── get_market_status.py
│   ├── screener/
│   │   ├── screen_stocks.py
│   │   └── get_stock_detail.py
│   ├── portfolio/
│   │   ├── manage_watchlist.py
│   │   └── manage_trades.py
│   └── admin/
│       └── refresh_screener.py   # Jobsをトリガー
└── dto/
    ├── market_dto.py
    ├── stock_dto.py
    └── trade_dto.py
```

**原則**:
- 1ユースケース = 1ファイル（単一責務）
- Domainの組み合わせでビジネスフローを実現
- Infrastructureへは Interface 経由でアクセス

---

### 3. Infrastructure Layer

**場所**: `backend/src/infrastructure/`

**責務**: 技術的詳細の実装（DB、外部API、ファイルシステム等）

**含まれるもの**:
- **Repository実装**: Domain の Repository Interface を実装
- **External Services**: 外部API連携（yfinance等）
- **Database**: DB接続、マイグレーション
- **Cache**: キャッシュ実装（将来）

```
infrastructure/
├── repositories/
│   ├── sqlalchemy_stock_repository.py
│   ├── sqlalchemy_trade_repository.py
│   └── sqlalchemy_watchlist_repository.py
├── external/
│   ├── yfinance_gateway.py       # yfinance連携
│   └── symbol_provider.py        # S&P500/NASDAQ100リスト取得
├── database/
│   ├── connection.py
│   ├── models.py                 # SQLAlchemyモデル
│   └── init.sql
└── cache/
    └── (将来実装)
```

**原則**:
- Domain の Interface を実装
- 技術的詳細をカプセル化
- 差し替え可能（テスト時にモック化）

---

### 4. Presentation Layer

**場所**: `backend/src/presentation/`

**責務**: 外部とのインターフェース（HTTP API、CLI等）

**含まれるもの**:
- **Controllers**: HTTPリクエスト/レスポンス処理
- **Schemas**: リクエスト/レスポンスのバリデーション
- **Middleware**: 認証、ロギング、エラーハンドリング

```
presentation/
├── api/
│   ├── market_controller.py
│   ├── screener_controller.py
│   ├── portfolio_controller.py
│   └── admin_controller.py
├── schemas/
│   ├── market_schema.py
│   ├── stock_schema.py
│   └── response_schema.py
└── middleware/
    ├── error_handler.py
    └── logging.py
```

**原則**:
- UseCaseを呼び出すだけ（ビジネスロジックなし）
- リクエスト検証とレスポンス整形
- HTTP固有の処理のみ

---

### 5. Jobs Layer（新規）

**場所**: `backend/src/jobs/`

**責務**: バックグラウンドジョブの実行、複数ジョブのオーケストレーション

**含まれるもの**:
- **lib/**: ジョブ共通基盤（基底クラス、エラー、コンテキスト）
- **executions/**: 個別ジョブ実装（単一責務）
- **flows/**: 複数ジョブのオーケストレーション

```
jobs/
├── lib/
│   ├── base.py           # Job基底クラス
│   ├── context.py        # 実行コンテキスト
│   └── errors.py         # ジョブ固有エラー
├── executions/
│   ├── collect_stock_data.py
│   ├── recalculate_rs_rating.py
│   └── recalculate_canslim.py
└── flows/
    └── refresh_screener.py
```

**原則**:
- Application Layer から Flow がトリガーされる
- Flow は executions を組み合わせる
- 各 execution は単一責務
- Domain の Entity/Service を使用可能
- Infrastructure へは Interface 経由

**Jobs と Application の違い**:

| 観点 | Application (UseCase) | Jobs |
|------|----------------------|------|
| 実行方式 | 同期（リクエスト/レスポンス） | 非同期（バックグラウンド） |
| 実行時間 | 短時間（秒単位） | 長時間可（分〜時間） |
| 呼び出し元 | Controller | UseCase or スケジューラ |
| 例 | GetStockDetail | CollectStockData |

---

## データフロー例

### 例1: スクリーニング結果取得（同期）

```
[Client]
    │
    │ GET /api/screener/canslim
    ▼
[ScreenerController]
    │
    │ screen_stocks_use_case.execute(filter)
    ▼
[ScreenStocksUseCase]
    │
    │ stock_repository.find_by_filter(filter)
    ▼
[SQLAlchemyStockRepository]
    │
    │ SELECT * FROM stocks WHERE ...
    ▼
[PostgreSQL]
```

### 例2: スクリーナーデータ更新（非同期）

```
[Client]
    │
    │ POST /api/admin/screener/refresh
    ▼
[AdminController]
    │
    │ background_tasks.add_task(flow.run)
    │ return {"status": "started"}
    ▼
[RefreshScreenerFlow]          ← Jobs Layer
    │
    ├─→ CollectStockDataJob    ← executions/
    │       │
    │       ├─→ MarketDataGateway.get_quote()
    │       └─→ StockRepository.upsert()
    │
    ├─→ RecalculateRSRatingJob
    │       │
    │       └─→ StockRepository.bulk_update()
    │
    └─→ RecalculateCANSLIMJob
            │
            └─→ StockRepository.bulk_update()
```

---

## ディレクトリ構成まとめ

```
backend/src/
├── domain/                    # 最内層：ビジネスルール
│   ├── entities/
│   ├── value_objects/
│   ├── services/
│   └── repositories/         # Interface定義
│
├── application/               # ユースケース
│   ├── use_cases/
│   └── dto/
│
├── infrastructure/            # 技術的実装
│   ├── repositories/         # Interface実装
│   ├── external/
│   └── database/
│
├── presentation/              # 外部インターフェース
│   ├── api/
│   ├── schemas/
│   └── middleware/
│
├── jobs/                      # バックグラウンドジョブ
│   ├── lib/
│   ├── executions/
│   └── flows/
│
└── main.py                    # エントリーポイント
```

---

## 関連ドキュメント

### レイヤー別詳細

- `docs/poc/architectures/layers/domain-layer.md` - Domain層 実装ガイド
- `docs/poc/architectures/layers/application-layer.md` - Application層 実装ガイド
- `docs/poc/architectures/layers/infrastructure-layer.md` - Infrastructure層 実装ガイド
- `docs/poc/architectures/layers/presentation-layer.md` - Presentation層 実装ガイド
- `docs/poc/architectures/layers/jobs-layer.md` - Jobs層 実装ガイド

### その他

- `docs/poc/plan/refresh-screener-usecase.md` - ジョブ設計詳細
- `docs/poc/coding-standard/` - コーディング規約
