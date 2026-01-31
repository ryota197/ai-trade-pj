# サービスコンポーネント設計（シンプル5層アーキテクチャ）

## 概要

本プロジェクトは「A Philosophy of Software Design」の原則に基づき、
**浅いモジュール（pass-through層）を排除したシンプルな5層アーキテクチャ**を採用する。

---

## アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frameworks & Drivers                          │
│         (FastAPI, PostgreSQL, yfinance, Web Browser)            │
├─────────────────────────────────────────────────────────────────┤
│                  Presentation + Jobs                             │
│           (Controllers, Schemas, Batch Flows)                   │
├─────────────────────────────────────────────────────────────────┤
│                      Queries                                     │
│                  (Data Access Layer)                            │
├────────────────────────┬────────────────────────────────────────┤
│       Services         │            Adapters                    │
│   (Business Logic)     │     (External Integrations)           │
├────────────────────────┴────────────────────────────────────────┤
│                        Models                                    │
│                 (ORM + Entity Methods)                          │
└─────────────────────────────────────────────────────────────────┘

依存の方向: 上位 → 下位（下位は上位を知らない）
```

---

## レイヤー構成

### 1. Models層（最下層）

**責務**: データ構造の定義、エンティティメソッド

- SQLAlchemy ORM モデル
- 状態変更メソッド（start, complete, fail等）
- 他のどのレイヤーにも依存しない

| 要素 | 説明 |
|------|------|
| ORM Model | テーブル定義（CANSLIMStock, Trade等） |
| Entity Methods | 状態管理ロジック（FlowExecution.start()等） |
| Enums | データ関連の列挙型（TradeType, WatchlistStatus等） |

---

### 2. Services層（ビジネスロジック）

**責務**: ビジネスルール、計算ロジック

- フレームワークに依存しない純粋なPythonコード
- Models層のみに依存

| 要素 | 説明 |
|------|------|
| Service | 計算ロジック（RSCalculator, CANSLIMScorer等） |
| Constants | ビジネス定数（CANSLIMDefaults, TradingDays） |
| Types (_lib/) | 型定義、値オブジェクト（MarketCondition, ScreeningCriteria） |

---

### 3. Queries層（データアクセス）

**責務**: データベースへのCRUD操作

- SQLAlchemyを使用したクエリ実装
- Models層、Adapters層に依存

| 要素 | 説明 |
|------|------|
| Query Class | データアクセスロジック（CANSLIMStockQuery等） |

---

### 4. Adapters層（外部連携）

**責務**: 外部サービス、データベース接続

- 外部ライブラリ（yfinance, SQLAlchemy等）に依存
- 他のレイヤーに依存しない

| 要素 | 説明 |
|------|------|
| Database | DB接続設定（engine, Base, get_db） |
| Gateway | 外部API連携（YFinanceGateway） |
| Provider | データプロバイダ（SymbolProvider） |

---

### 5. Presentation層（API）

**責務**: HTTPリクエスト/レスポンスの処理

- Queries/Servicesを直接呼び出す
- ORM Model → Schema変換を担当

| 要素 | 説明 |
|------|------|
| Controller | APIエンドポイント定義 |
| Schema | Pydanticスキーマ（リクエスト/レスポンス） |
| Dependencies | 依存性注入設定 |

---

### 6. Jobs層（バッチ処理）

**責務**: 長時間バッチ処理のオーケストレーション

- Queries/Adaptersを直接利用
- 管理画面からトリガーで実行

| 要素 | 説明 |
|------|------|
| Flow | 複数Jobのオーケストレーション（RefreshScreenerFlow） |
| Job | 個別の処理単位（CollectStockDataJob等） |

---

## ディレクトリ構成

```
backend/src/
├── models/               # ORM models + entity methods
│   ├── canslim_stock.py
│   ├── trade.py
│   ├── watchlist.py
│   ├── market_snapshot.py
│   ├── flow_execution.py
│   └── job_execution.py
│
├── services/             # Business logic
│   ├── _lib/             # Types, value objects
│   │   ├── types.py
│   │   └── screening_criteria.py
│   ├── constants/        # Business constants
│   │   ├── canslim_defaults.py
│   │   └── trading_days.py
│   ├── rs_calculator.py
│   ├── rs_rating_calculator.py
│   ├── canslim_scorer.py
│   └── market_analyzer.py
│
├── queries/              # Data access
│   ├── canslim_stock.py
│   ├── trade.py
│   ├── watchlist.py
│   ├── market_snapshot.py
│   ├── flow_execution.py
│   └── job_execution.py
│
├── adapters/             # External integrations
│   ├── database.py
│   ├── yfinance.py
│   └── symbol_provider.py
│
├── presentation/         # API layer
│   ├── controllers/
│   ├── schemas/
│   └── dependencies.py
│
├── jobs/                 # Batch processing
│   ├── executions/
│   ├── flows/
│   └── lib/
│
├── main.py
└── config.py
```

---

## 依存関係の方向

```
presentation ──> queries ──> models
      │              ↓
      │          adapters
      ↓
   services ──────> models
      │
   jobs ───────────────┘
```

**許可される依存:**
- presentation → queries, services, models, schemas
- queries → models, adapters
- services → models（ORM を引数として受け取る）
- jobs → queries, services, models, adapters
- adapters → (外部ライブラリのみ)

**禁止される依存:**
- models → 他のどの層にも依存しない
- services → queries, adapters に依存しない
- adapters → models, queries, services に依存しない

---

## 設計原則

### YAGNI適用箇所

1. **抽象インターフェース削除**: Repository/Gateway抽象クラス不要
2. **Application層削除**: UseCase層はpass-throughのため不要
3. **薄いロジックのインライン化**: 1-3行の計算はヘルパー関数として呼び出し側に配置

### ORM モデルの拡張

FlowExecution, JobExecution等の状態管理が必要なモデルには、
エンティティメソッドを直接定義する。

```python
class FlowExecution(Base):
    # ... ORM定義 ...

    def start(self, first_job: str) -> None:
        self.status = "running"
        self.started_at = datetime.now(timezone.utc)
```

---

## 関連ドキュメント

| ドキュメント | 内容 |
|-------------|------|
| [directory-structure.md](./directory-structure.md) | ディレクトリ構成 |
| [backend-guidelines.md](../coding-standard/backend-guidelines.md) | バックエンドコーディング規約 |
