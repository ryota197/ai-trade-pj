# ディレクトリ構成（クリーンアーキテクチャ）

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
├── backend/                     # FastAPI アプリ（クリーンアーキテクチャ）
│   └── ...
│
└── ml/                          # ML関連（Phase 2以降）
    └── ...
```

---

## Backend（クリーンアーキテクチャ）

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
│   ├── domain/                  # ドメイン層（最内層）
│   │   ├── __init__.py
│   │   │
│   │   ├── entities/            # エンティティ
│   │   │   ├── __init__.py
│   │   │   ├── stock.py
│   │   │   ├── market_status.py
│   │   │   ├── watchlist_item.py
│   │   │   └── paper_trade.py
│   │   │
│   │   ├── value_objects/       # 値オブジェクト
│   │   │   ├── __init__.py
│   │   │   ├── canslim_score.py
│   │   │   ├── price_data.py
│   │   │   └── market_indicators.py
│   │   │
│   │   ├── services/            # ドメインサービス
│   │   │   ├── __init__.py
│   │   │   ├── market_analyzer.py
│   │   │   ├── rs_rating_calculator.py
│   │   │   └── performance_calculator.py
│   │   │
│   │   └── repositories/        # リポジトリインターフェース（抽象）
│   │       ├── __init__.py
│   │       ├── stock_repository.py
│   │       ├── market_data_repository.py
│   │       ├── watchlist_repository.py
│   │       └── trade_repository.py
│   │
│   ├── application/             # アプリケーション層（ユースケース）
│   │   ├── __init__.py
│   │   │
│   │   ├── use_cases/           # ユースケース
│   │   │   ├── __init__.py
│   │   │   │
│   │   │   ├── market/          # マーケット関連
│   │   │   │   ├── __init__.py
│   │   │   │   ├── get_market_status.py
│   │   │   │   └── get_market_indicators.py
│   │   │   │
│   │   │   ├── screener/        # スクリーナー関連
│   │   │   │   ├── __init__.py
│   │   │   │   ├── screen_canslim_stocks.py
│   │   │   │   └── get_stock_detail.py
│   │   │   │
│   │   │   ├── portfolio/       # ポートフォリオ関連
│   │   │   │   ├── __init__.py
│   │   │   │   ├── manage_watchlist.py
│   │   │   │   ├── record_trade.py
│   │   │   │   └── get_performance.py
│   │   │   │
│   │   │   └── data/            # データ取得関連
│   │   │       ├── __init__.py
│   │   │       ├── get_stock_quote.py
│   │   │       └── get_price_history.py
│   │   │
│   │   ├── dto/                 # Data Transfer Objects
│   │   │   ├── __init__.py
│   │   │   ├── market_dto.py
│   │   │   ├── screener_dto.py
│   │   │   └── portfolio_dto.py
│   │   │
│   │   └── interfaces/          # 外部サービスのインターフェース
│   │       ├── __init__.py
│   │       ├── financial_data_gateway.py
│   │       └── price_data_gateway.py
│   │
│   ├── infrastructure/          # インフラストラクチャ層
│   │   ├── __init__.py
│   │   │
│   │   ├── database/            # データベース関連
│   │   │   ├── __init__.py
│   │   │   ├── connection.py    # DB接続設定
│   │   │   ├── models/          # SQLAlchemyモデル
│   │   │   │   ├── __init__.py
│   │   │   │   ├── market_snapshot_model.py
│   │   │   │   ├── screener_result_model.py
│   │   │   │   ├── watchlist_model.py
│   │   │   │   ├── paper_trade_model.py
│   │   │   │   └── price_cache_model.py
│   │   │   └── migrations/      # マイグレーション（将来）
│   │   │
│   │   ├── repositories/        # リポジトリ実装
│   │   │   ├── __init__.py
│   │   │   ├── postgres_stock_repository.py
│   │   │   ├── postgres_watchlist_repository.py
│   │   │   └── postgres_trade_repository.py
│   │   │
│   │   └── gateways/            # 外部API連携（ゲートウェイ実装）
│   │       ├── __init__.py
│   │       ├── yfinance_market_data_gateway.py
│   │       ├── yfinance_price_gateway.py
│   │       ├── fmp_financial_gateway.py
│   │       └── sec_edgar_gateway.py
│   │
│   └── presentation/            # プレゼンテーション層
│       ├── __init__.py
│       │
│       ├── api/                 # FastAPI ルーター
│       │   ├── __init__.py
│       │   ├── market_controller.py
│       │   ├── screener_controller.py
│       │   ├── data_controller.py
│       │   └── portfolio_controller.py
│       │
│       ├── schemas/             # Pydantic スキーマ（APIリクエスト/レスポンス）
│       │   ├── __init__.py
│       │   ├── common.py        # 共通スキーマ（ApiResponse等）
│       │   ├── market.py
│       │   ├── screener.py
│       │   ├── data.py
│       │   └── portfolio.py
│       │
│       └── dependencies.py      # 依存性注入設定
│
└── tests/                       # テスト
    ├── __init__.py
    ├── conftest.py              # pytest設定
    │
    ├── domain/                  # ドメイン層テスト
    │   ├── test_market_analyzer.py
    │   ├── test_canslim_score.py
    │   └── test_rs_rating_calculator.py
    │
    ├── application/             # ユースケーステスト
    │   ├── test_get_market_status.py
    │   └── test_screen_canslim_stocks.py
    │
    ├── infrastructure/          # インフラ層テスト（統合テスト）
    │   ├── test_yfinance_gateway.py
    │   └── test_postgres_repository.py
    │
    └── presentation/            # API テスト（E2E）
        └── test_api_endpoints.py
```

---

## レイヤー間の依存関係

```
tests/
   │
   ├── domain/          → テスト対象: domain/
   ├── application/     → テスト対象: application/ + domain/（モック）
   ├── infrastructure/  → テスト対象: infrastructure/ + 実DB/API
   └── presentation/    → テスト対象: 全レイヤー統合

src/
   │
   ├── presentation/    → 依存: application, (infrastructure via DI)
   │       ↓
   ├── application/     → 依存: domain
   │       ↓
   ├── domain/          → 依存: なし（最内層）
   │       ↑
   └── infrastructure/  → 実装: domain/repositories, application/interfaces
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
    │   ├── stock/
    │   │   └── [symbol]/
    │   │       └── page.tsx
    │   │
    │   └── portfolio/
    │       └── page.tsx
    │
    ├── components/              # UIコンポーネント
    │   ├── charts/
    │   │   ├── PriceChart.tsx
    │   │   └── index.ts
    │   │
    │   ├── market/
    │   │   ├── MarketStatus.tsx
    │   │   ├── IndicatorCard.tsx
    │   │   └── index.ts
    │   │
    │   ├── screener/
    │   │   ├── StockTable.tsx
    │   │   ├── FilterPanel.tsx
    │   │   └── index.ts
    │   │
    │   ├── portfolio/
    │   │   ├── WatchlistTable.tsx
    │   │   ├── TradeForm.tsx
    │   │   └── index.ts
    │   │
    │   └── ui/
    │       ├── Button.tsx
    │       ├── Card.tsx
    │       └── index.ts
    │
    ├── hooks/                   # カスタムフック
    │   ├── useMarketStatus.ts
    │   ├── useScreener.ts
    │   ├── useStockData.ts
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

## ML (Phase 2以降)

```
ml/
├── notebooks/                   # 実験用Jupyter
│   ├── 01_data_exploration.ipynb
│   ├── 02_pattern_detection.ipynb
│   └── 03_model_training.ipynb
│
├── models/                      # 学習済みモデル
│   └── pattern_detector_v1.pt
│
├── data/                        # 学習データ
│   ├── raw/
│   └── processed/
│
└── src/
    ├── __init__.py
    ├── dataset.py
    ├── model.py
    ├── train.py
    └── inference.py
```

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
      - ./backend/src/infrastructure/database/init.sql:/docker-entrypoint-initdb.d/init.sql

volumes:
  postgres_data:
```

### .env.example

```bash
# Database
DATABASE_URL=postgresql://trader:localdev@localhost:5432/trading

# External APIs
FMP_API_KEY=your_api_key_here

# App
DEBUG=true
LOG_LEVEL=INFO
```

### .gitignore

```gitignore
# Dependencies
node_modules/
__pycache__/
*.pyc
.venv/
venv/

# Build
.next/
dist/
build/

# Environment
.env
.env.local

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db

# Data
*.csv
*.parquet
ml/data/raw/
ml/models/*.pt

# Logs
*.log
logs/

# Test
.coverage
htmlcov/
.pytest_cache/
```

---

## モジュールの命名規則

| レイヤー | 命名パターン | 例 |
|---------|-------------|-----|
| Entity | `{名詞}.py` | `stock.py`, `market_status.py` |
| Value Object | `{名詞}.py` | `canslim_score.py` |
| Domain Service | `{名詞}_calculator.py`, `{名詞}_analyzer.py` | `market_analyzer.py` |
| Repository Interface | `{名詞}_repository.py` | `stock_repository.py` |
| Use Case | `{動詞}_{名詞}.py` | `get_market_status.py`, `screen_canslim_stocks.py` |
| Gateway Interface | `{名詞}_gateway.py` | `financial_data_gateway.py` |
| Repository Impl | `postgres_{名詞}_repository.py` | `postgres_stock_repository.py` |
| Gateway Impl | `{provider}_{名詞}_gateway.py` | `yfinance_market_data_gateway.py` |
| Controller | `{名詞}_controller.py` | `market_controller.py` |
| Schema | `{名詞}.py` | `market.py`, `screener.py` |
