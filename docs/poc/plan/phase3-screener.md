# Phase 3: Screener Module

## 目的

CAN-SLIM条件に基づいて銘柄をスクリーニングし、投資候補を抽出する。
個別銘柄の詳細情報を表示し、投資判断をサポートする。

---

## ゴール

- CAN-SLIM条件でフィルタリングされた銘柄一覧が表示される
- フィルター条件をカスタマイズできる
- 個別銘柄の詳細ページでチャート・財務データが確認できる

---

## タスク

### 3.1 Domain層実装

- [ ] `Stock` Entity作成
- [ ] `CANSLIMScore` Value Object作成
- [ ] `StockRepository` Interface作成
- [ ] RS Rating計算ロジック作成

**成果物**:
```
backend/src/domain/
├── entities/
│   └── stock.py
├── value_objects/
│   └── canslim_score.py
├── services/
│   └── rs_rating_calculator.py
└── repositories/
    └── stock_repository.py
```

---

### 3.2 Application層実装

- [ ] `ScreenCANSLIMStocksUseCase` 作成
- [ ] `GetStockDetailUseCase` 作成
- [ ] `GetPriceHistoryUseCase` 作成
- [ ] `FinancialDataGateway` Interface作成
- [ ] 入出力DTO定義

**成果物**:
```
backend/src/application/
├── use_cases/
│   └── screener/
│       ├── screen_canslim_stocks.py
│       ├── get_stock_detail.py
│       └── get_price_history.py
├── interfaces/
│   └── financial_data_gateway.py
└── dto/
    └── screener_dto.py
```

---

### 3.3 Infrastructure層実装

- [ ] `YFinancePriceGateway` 実装（株価履歴）
- [ ] `FMPFinancialGateway` 実装（財務データ）※またはyfinanceで代用
- [ ] `ScreenerResultModel` SQLAlchemyモデル作成
- [ ] `PriceCacheModel` SQLAlchemyモデル作成
- [ ] `PostgresScreenerRepository` 実装

**成果物**:
```
backend/src/infrastructure/
├── gateways/
│   ├── yfinance_price_gateway.py
│   └── fmp_financial_gateway.py
├── repositories/
│   └── postgres_screener_repository.py
└── database/
    └── models/
        ├── screener_result_model.py
        └── price_cache_model.py
```

---

### 3.4 Presentation層実装

- [ ] `screener_controller.py` ルーター作成
- [ ] `GET /api/screener/canslim` エンドポイント
- [ ] `GET /api/data/quote/{symbol}` エンドポイント（Phase 1で作成済み）
- [ ] `GET /api/data/history/{symbol}` エンドポイント
- [ ] `GET /api/data/financials/{symbol}` エンドポイント
- [ ] Pydanticスキーマ定義

**成果物**:
```
backend/src/presentation/
├── api/
│   ├── screener_controller.py
│   └── data_controller.py
└── schemas/
    ├── screener.py
    └── data.py
```

**API確認**:
```bash
curl "http://localhost:8000/api/screener/canslim?min_rs_rating=80&limit=20"
# {
#   "success": true,
#   "data": {
#     "count": 15,
#     "stocks": [
#       {"symbol": "NVDA", "rs_rating": 98, "canslim_score": 95, ...}
#     ]
#   }
# }
```

---

### 3.5 Frontend - スクリーナーUI

- [ ] `app/screener/page.tsx` スクリーナーページ作成
- [ ] `StockTable` コンポーネント作成
- [ ] `FilterPanel` コンポーネント作成
- [ ] `useScreener` カスタムフック作成
- [ ] フィルター状態管理

**成果物**:
```
frontend/src/
├── app/
│   └── screener/
│       └── page.tsx
├── components/
│   └── screener/
│       ├── StockTable.tsx
│       ├── FilterPanel.tsx
│       └── index.ts
├── hooks/
│   └── useScreener.ts
└── types/
    └── stock.ts
```

**UI要素**:
- フィルターパネル（EPS成長率、RS Rating、出来高倍率）
- 銘柄一覧テーブル（Symbol, Name, Price, RS Rating, CAN-SLIMスコア）
- ソート機能
- ページネーション（必要に応じて）

---

### 3.6 Frontend - 個別銘柄詳細ページ

- [ ] `app/stock/[symbol]/page.tsx` 詳細ページ作成
- [ ] `PriceChart` コンポーネント作成（Lightweight Charts）
- [ ] `FundamentalsCard` コンポーネント作成
- [ ] `CANSLIMScoreCard` コンポーネント作成
- [ ] `useStockData` カスタムフック作成

**成果物**:
```
frontend/src/
├── app/
│   └── stock/
│       └── [symbol]/
│           └── page.tsx
├── components/
│   ├── charts/
│   │   └── PriceChart.tsx
│   └── stock/
│       ├── FundamentalsCard.tsx
│       ├── CANSLIMScoreCard.tsx
│       └── index.ts
└── hooks/
    └── useStockData.ts
```

**UI要素**:
- 株価チャート（日足、出来高）
- CAN-SLIMスコア表示
- 財務指標（EPS成長率、PER、時価総額等）
- 52週高値からの乖離率

---

## CAN-SLIM スクリーニング条件

| 項目 | 条件 | デフォルト値 |
|------|------|-------------|
| C - Current Quarterly Earnings | EPS成長率（四半期） | ≥ 25% |
| A - Annual Earnings | EPS成長率（年間） | ≥ 25% |
| N - New High | 52週高値からの乖離 | ≤ 15% |
| S - Supply and Demand | 出来高倍率 | ≥ 1.5x |
| L - Leader | RS Rating | ≥ 80 |
| I - Institutional | 機関投資家保有率 | 参考値として表示 |
| M - Market Direction | Phase 2のMarket状態 | Risk On時にスクリーニング推奨 |

---

## 完了条件

| # | 条件 | 確認方法 |
|---|------|----------|
| 1 | Screener APIが動作 | `GET /api/screener/canslim` が銘柄リストを返す |
| 2 | フィルターが機能する | パラメータ変更で結果が変わる |
| 3 | スクリーナーUIが表示 | `http://localhost:3000/screener` で一覧表示 |
| 4 | 詳細ページが表示 | `http://localhost:3000/stock/AAPL` でチャート表示 |
| 5 | チャートが描画される | Lightweight Chartsで株価チャート表示 |

---

## 次のフェーズへ

Phase 3 完了後 → [Phase 4: Portfolio Module](./phase4-portfolio.md)
