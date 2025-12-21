# ファイルリファレンス

## 概要

ファイルを探すためのクイックリファレンス。

---

## バックエンド構成

```
backend/src/
├── main.py                    # FastAPIエントリーポイント
├── config.py                  # 設定（DB接続URL、API prefix等）
│
├── presentation/              # === Presentation層 ===
│   ├── api/
│   │   ├── screener_controller.py   # GET /screener/canslim, /stock/{symbol}
│   │   ├── market_controller.py     # GET /market/status, /indicators
│   │   ├── data_controller.py       # GET /data/quote, /history, /financials
│   │   └── health_controller.py     # GET /health
│   ├── dependencies.py              # DI設定（UseCase生成）
│   └── schemas/
│       ├── common.py          # ApiResponse, ErrorDetail
│       ├── screener.py        # ScreenerResponse, StockDetailSchema
│       ├── market.py          # MarketStatusResponse
│       ├── quote.py           # QuoteResponse, HistoryResponse
│       └── health.py          # HealthResponse
│
├── application/               # === Application層 ===
│   ├── use_cases/
│   │   ├── data/
│   │   │   └── get_financial_metrics.py  # 財務指標取得（EPS成長率計算含む）
│   │   ├── screener/
│   │   │   ├── screen_canslim_stocks.py  # CAN-SLIMスクリーニング
│   │   │   ├── get_stock_detail.py       # 銘柄詳細取得
│   │   │   └── get_price_history.py      # 株価履歴取得
│   │   └── market/
│   │       ├── get_market_status.py      # マーケット状態取得
│   │       └── get_market_indicators.py  # マーケット指標取得
│   ├── dto/
│   │   ├── screener_dto.py    # ScreenerFilterInput, StockDetailOutput等
│   │   └── market_dto.py      # MarketStatusOutput等
│   └── interfaces/
│       └── financial_data_gateway.py  # FinancialDataGateway IF, RawFinancialData
│
├── domain/                    # === Domain層 ===
│   ├── entities/
│   │   ├── stock.py           # Stock, StockSummary
│   │   ├── market_status.py   # MarketStatus, MarketCondition
│   │   └── quote.py           # Quote, HistoricalPrice
│   ├── value_objects/
│   │   ├── canslim_score.py   # CANSLIMScore, CANSLIMCriteria
│   │   └── market_indicators.py  # MarketIndicators, VIXIndicator等
│   ├── services/
│   │   ├── eps_growth_calculator.py  # EPS成長率計算
│   │   ├── market_analyzer.py        # マーケット状態分析
│   │   └── rs_rating_calculator.py   # RS Rating計算
│   ├── repositories/
│   │   ├── stock_repository.py          # StockRepository IF
│   │   ├── market_data_repository.py    # MarketDataRepository IF
│   │   └── market_snapshot_repository.py
│   └── constants/
│       └── canslim_thresholds.py  # CAN-SLIM閾値定数
│
└── infrastructure/            # === Infrastructure層 ===
    ├── gateways/
    │   ├── yfinance_gateway.py           # 株価・財務データ取得
    │   └── yfinance_market_data_gateway.py # VIX・RSI等取得
    ├── repositories/
    │   ├── postgres_screener_repository.py  # スクリーナーDB操作
    │   └── postgres_market_repository.py    # マーケットDB操作
    └── database/
        ├── connection.py      # DB接続、get_db()
        ├── init.sql           # DDL（テーブル定義）
        └── models/
            ├── screener_result_model.py  # ScreenerResultModel
            ├── market_snapshot_model.py  # MarketSnapshotModel
            └── price_cache_model.py      # PriceCacheModel
```

---

## フロントエンド構成

```
frontend/src/
├── app/                       # === Pages (App Router) ===
│   ├── layout.tsx             # 共通レイアウト
│   ├── page.tsx               # / ホーム（ダッシュボード）
│   ├── screener/
│   │   └── page.tsx           # /screener スクリーナー
│   └── stock/
│       └── [symbol]/
│           └── page.tsx       # /stock/:symbol 銘柄詳細
│
├── components/                # === Components ===
│   ├── layout/
│   │   └── Header.tsx         # ヘッダー
│   ├── market/
│   │   ├── MarketDashboard.tsx  # ダッシュボード全体
│   │   ├── MarketStatus.tsx     # Risk On/Off表示
│   │   └── IndicatorCard.tsx    # 個別指標カード
│   ├── screener/
│   │   ├── StockTable.tsx     # 銘柄一覧テーブル
│   │   └── FilterPanel.tsx    # フィルター設定
│   ├── stock/
│   │   ├── FundamentalsCard.tsx   # 財務指標カード
│   │   └── CANSLIMScoreCard.tsx   # CAN-SLIMスコア表示
│   ├── charts/
│   │   └── PriceChart.tsx     # 株価チャート（Lightweight Charts）
│   └── ui/
│       ├── card.tsx           # Cardコンポーネント
│       ├── badge.tsx          # Badgeコンポーネント
│       ├── button.tsx         # Buttonコンポーネント
│       ├── ModuleCard.tsx     # モジュールカード
│       └── StatusCard.tsx     # ステータスカード
│
├── hooks/                     # === Custom Hooks ===
│   ├── useMarketStatus.ts     # マーケット状態取得
│   ├── useScreener.ts         # スクリーニング
│   └── useStockData.ts        # 銘柄データ取得
│
├── lib/                       # === Utilities ===
│   ├── api.ts                 # APIクライアント
│   └── utils.ts               # ユーティリティ関数
│
└── types/                     # === Type Definitions ===
    ├── api.ts                 # ApiResponse, HealthResponse
    ├── market.ts              # MarketStatusResponse等
    └── stock.ts               # Stock, CANSLIMScore等
```

---

## 主要ファイル早見表

### 「〇〇を変更したい」時に見るファイル

| やりたいこと | ファイル |
|-------------|---------|
| APIエンドポイントを追加 | `presentation/api/*_controller.py` |
| ビジネスロジックを変更 | `domain/services/*.py` |
| DB操作を変更 | `infrastructure/repositories/*.py` |
| 外部API呼び出しを変更 | `infrastructure/gateways/*.py` |
| テーブル定義を変更 | `infrastructure/database/init.sql` |
| フロントのページを追加 | `app/*/page.tsx` |
| API呼び出しを変更 | `lib/api.ts` |
| 型定義を変更 | `types/*.ts` |

### 「〇〇の処理がどこにあるか」を探す

| 機能 | バックエンド | フロントエンド |
|------|-------------|---------------|
| CAN-SLIMスクリーニング | `screen_canslim_stocks.py` | `useScreener.ts` |
| マーケット状態判定 | `market_analyzer.py` | `useMarketStatus.ts` |
| RS Rating計算 | `rs_rating_calculator.py` | - |
| EPS成長率計算 | `eps_growth_calculator.py` | - |
| 財務指標取得 | `get_financial_metrics.py` | `useStockData.ts` |
| 株価チャート表示 | - | `PriceChart.tsx` |
| フィルター設定 | `ScreenerFilter` | `FilterPanel.tsx` |

---

## レイヤー間の呼び出し関係

```
Frontend                    Backend
─────────────────────────────────────────────────
Page
  ↓
Hook ────────→ api.ts ────→ Controller
                              ↓
                            UseCase
                              ↓
                        ┌─────┴─────┐
                        ↓           ↓
                   Repository    Gateway
                        ↓           ↓
                   PostgreSQL   yfinance
```
