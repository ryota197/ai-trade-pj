# ディレクトリ構成（シンプル5層アーキテクチャ）

## 全体構成

```
ai-trade-app/
├── docker-compose.yml          # Docker構成
├── .env.example                 # 環境変数サンプル
├── .gitignore
├── README.md
│
├── docs/                        # ドキュメント
│   ├── ideas/                   # アイディア・企画
│   └── poc/                     # PoC設計ドキュメント
│       ├── overview.md
│       ├── architectures/
│       └── coding-standard/
│
├── frontend/                    # Next.js アプリ
│   └── ...
│
├── backend/                     # FastAPI アプリ（5層アーキテクチャ）
│   └── ...
│
└── ml/                          # ML関連（Phase 2以降）
    └── ...
```

---

## Backend（シンプル5層アーキテクチャ）

```
backend/
├── pyproject.toml               # プロジェクト設定
├── requirements.txt             # 依存関係
├── .python-version              # Pythonバージョン
│
├── src/
│   ├── __init__.py
│   ├── main.py                  # FastAPI エントリーポイント
│   ├── config.py                # 設定管理
│   │
│   ├── models/                  # ORM モデル層（最下層）
│   │   ├── __init__.py
│   │   ├── canslim_stock.py     # CAN-SLIM銘柄
│   │   ├── trade.py             # トレード + TradeType, TradeStatus
│   │   ├── watchlist.py         # ウォッチリスト + WatchlistStatus
│   │   ├── market_snapshot.py   # マーケットスナップショット
│   │   ├── flow_execution.py    # フロー実行（エンティティメソッド含む）
│   │   └── job_execution.py     # ジョブ実行（エンティティメソッド含む）
│   │
│   ├── services/                # ビジネスロジック層
│   │   ├── __init__.py
│   │   │
│   │   ├── _lib/                # 内部ライブラリ（型定義・値オブジェクト）
│   │   │   ├── __init__.py
│   │   │   ├── types.py         # MarketCondition, Signal, MarketAnalysisResult
│   │   │   └── screening_criteria.py
│   │   │
│   │   ├── constants/           # ビジネス定数
│   │   │   ├── __init__.py
│   │   │   ├── canslim_defaults.py
│   │   │   └── trading_days.py
│   │   │
│   │   ├── rs_calculator.py     # RS計算
│   │   ├── rs_rating_calculator.py  # RSレーティング計算
│   │   ├── canslim_scorer.py    # CAN-SLIMスコア計算
│   │   └── market_analyzer.py   # マーケット分析
│   │
│   ├── queries/                 # データアクセス層
│   │   ├── __init__.py
│   │   ├── canslim_stock.py     # CANSLIMStockQuery
│   │   ├── trade.py             # TradeQuery
│   │   ├── watchlist.py         # WatchlistQuery
│   │   ├── market_snapshot.py   # MarketSnapshotQuery
│   │   ├── flow_execution.py    # FlowExecutionQuery
│   │   └── job_execution.py     # JobExecutionQuery
│   │
│   ├── adapters/                # 外部連携層
│   │   ├── __init__.py
│   │   ├── database.py          # DB接続（engine, Base, get_db）
│   │   ├── yfinance.py          # yfinance連携（Gateway + データクラス）
│   │   └── symbol_provider.py   # シンボルプロバイダ
│   │
│   ├── presentation/            # プレゼンテーション層
│   │   ├── __init__.py
│   │   │
│   │   ├── controllers/         # APIエンドポイント
│   │   │   ├── __init__.py
│   │   │   ├── health_controller.py
│   │   │   ├── market_controller.py
│   │   │   ├── screener_controller.py
│   │   │   ├── portfolio_controller.py
│   │   │   └── admin_controller.py
│   │   │
│   │   ├── schemas/             # Pydantic スキーマ
│   │   │   ├── __init__.py
│   │   │   ├── common.py
│   │   │   ├── health.py
│   │   │   ├── market.py
│   │   │   ├── screener.py
│   │   │   ├── portfolio.py
│   │   │   └── admin.py
│   │   │
│   │   └── dependencies.py      # 依存性注入設定
│   │
│   └── jobs/                    # バッチ処理層
│       ├── __init__.py
│       │
│       ├── executions/          # ジョブ実装
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── collect_stock_data.py
│       │   ├── calculate_rs_rating.py
│       │   └── calculate_canslim.py
│       │
│       ├── flows/               # フロー定義
│       │   ├── __init__.py
│       │   └── refresh_screener.py
│       │
│       └── lib/                 # ジョブ共通基盤
│           ├── __init__.py
│           └── models.py        # FlowStatus, JobStatus enums
│
└── tests/                       # テスト
    └── ...
```

---

## レイヤー間の依存関係

```
src/
   │
   ├── presentation/    → 依存: queries, services, models
   │       ↓
   ├── queries/         → 依存: models, adapters
   │       ↓
   ├── services/        → 依存: models のみ
   │       ↓
   ├── models/          → 依存: adapters.database (Base)
   │
   └── adapters/        → 依存: 外部ライブラリのみ

jobs/ → queries, services, models, adapters に依存
```

---

## Frontend (Next.js)

フロントエンドはシンプルな構成を維持。

```
frontend/
├── package.json
├── next.config.js
├── tsconfig.json
├── tailwind.config.js
│
└── src/
    ├── app/                     # App Router（ページ）
    │   ├── layout.tsx
    │   ├── page.tsx             # Dashboard
    │   ├── globals.css
    │   │
    │   ├── screener/
    │   │   └── page.tsx
    │   │
    │   └── portfolio/
    │       └── page.tsx
    │
    ├── components/              # UIコンポーネント
    │   ├── charts/
    │   ├── market/
    │   ├── screener/
    │   ├── portfolio/
    │   └── ui/
    │
    ├── hooks/                   # カスタムフック
    │   ├── useMarketStatus.ts
    │   ├── useScreener.ts
    │   └── index.ts
    │
    ├── lib/                     # ユーティリティ
    │   ├── api.ts               # APIクライアント
    │   ├── utils.ts
    │   └── constants.ts
    │
    └── types/                   # 型定義
        ├── market.ts
        ├── stock.ts
        ├── portfolio.ts
        └── index.ts
```

---

## モジュールの命名規則

| レイヤー | 命名パターン | 例 |
|---------|-------------|-----|
| ORM Model | `{名詞}.py` | `canslim_stock.py`, `trade.py` |
| Service | `{名詞}_calculator.py`, `{名詞}_scorer.py` | `rs_calculator.py` |
| Query | `{名詞}.py` (クラス名: `{名詞}Query`) | `canslim_stock.py` → `CANSLIMStockQuery` |
| Adapter | `{名詞}.py` | `database.py`, `yfinance.py` |
| Controller | `{名詞}_controller.py` | `market_controller.py` |
| Schema | `{名詞}.py` | `market.py`, `screener.py` |
| Job | `{動詞}_{名詞}.py` | `collect_stock_data.py` |
| Flow | `{動詞}_{名詞}.py` | `refresh_screener.py` |

---

## 設定ファイル

### docker-compose.yml

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

volumes:
  postgres_data:
```

### .env.example

```bash
# Database
DATABASE_URL=postgresql://trader:localdev@localhost:5432/trading

# App
DEBUG=true
LOG_LEVEL=INFO
```
