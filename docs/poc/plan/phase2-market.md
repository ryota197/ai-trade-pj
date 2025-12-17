# Phase 2: Market Module

## 目的

マーケット全体の環境を可視化し、Risk On/Off/Neutralの判定を行う。
CAN-SLIM投資において「M（Market Direction）」の判断材料を提供する。

---

## ゴール

- VIX、Put/Call Ratio、S&P500 RSI等の指標が表示される
- マーケット状態（Risk On/Off/Neutral）が判定される
- ダッシュボードUIで市場環境が一目でわかる

---

## タスク

### 2.1 Domain層実装

- [ ] `MarketCondition` Enum作成（risk_on, risk_off, neutral）
- [ ] `MarketStatus` Entity作成
- [ ] `MarketIndicators` Value Object作成
- [ ] `MarketAnalyzer` Domain Service作成（判定ロジック）
- [ ] `MarketDataRepository` Interface作成

**成果物**:
```
backend/src/domain/
├── entities/
│   └── market_status.py
├── value_objects/
│   └── market_indicators.py
├── services/
│   └── market_analyzer.py
└── repositories/
    └── market_data_repository.py
```

---

### 2.2 Application層実装

- [ ] `GetMarketStatusUseCase` 作成
- [ ] `GetMarketIndicatorsUseCase` 作成
- [ ] 出力DTO定義

**成果物**:
```
backend/src/application/
├── use_cases/
│   └── market/
│       ├── get_market_status.py
│       └── get_market_indicators.py
└── dto/
    └── market_dto.py
```

---

### 2.3 Infrastructure層実装

- [ ] `YFinanceMarketDataGateway` 実装（VIX, S&P500取得）
- [ ] `MarketSnapshotModel` SQLAlchemyモデル作成
- [ ] `PostgresMarketRepository` 実装（履歴保存）

**成果物**:
```
backend/src/infrastructure/
├── gateways/
│   └── yfinance_market_data_gateway.py
├── repositories/
│   └── postgres_market_repository.py
└── database/
    └── models/
        └── market_snapshot_model.py
```

---

### 2.4 Presentation層実装

- [ ] `market_controller.py` ルーター作成
- [ ] `GET /api/market/status` エンドポイント
- [ ] `GET /api/market/indicators` エンドポイント
- [ ] Pydanticスキーマ定義
- [ ] 依存性注入設定

**成果物**:
```
backend/src/presentation/
├── api/
│   └── market_controller.py
├── schemas/
│   └── market.py
└── dependencies.py
```

**API確認**:
```bash
curl http://localhost:8000/api/market/status
# {
#   "success": true,
#   "data": {
#     "status": "risk_on",
#     "confidence": 0.75,
#     "recommendation": "市場環境は良好。個別株のエントリー検討可。",
#     ...
#   }
# }
```

---

### 2.5 Frontend - ダッシュボードUI

- [ ] `app/page.tsx` ダッシュボードページ実装
- [ ] `MarketStatus` コンポーネント作成
- [ ] `IndicatorCard` コンポーネント作成
- [ ] `useMarketStatus` カスタムフック作成
- [ ] API連携実装
- [ ] TailwindCSSでスタイリング

**成果物**:
```
frontend/src/
├── app/
│   └── page.tsx              # Dashboard
├── components/
│   └── market/
│       ├── MarketStatus.tsx
│       ├── IndicatorCard.tsx
│       └── index.ts
├── hooks/
│   └── useMarketStatus.ts
└── types/
    └── market.ts
```

**UI要素**:
- マーケット状態バッジ（Risk On: 緑, Off: 赤, Neutral: 黄）
- VIXカード（値、シグナル）
- S&P500 RSIカード（値、シグナル）
- Put/Call Ratioカード
- 推奨アクションテキスト

---

## 判定ロジック

### マーケット状態判定

| 指標 | Bullish条件 | Bearish条件 | スコア |
|------|------------|------------|-------|
| VIX | < 20 | > 30 | ±2 |
| S&P500 RSI | 30-70 | < 30 or > 70 | ±1 |
| S&P500 vs 200MA | 上回る | 下回る | ±1 |
| Put/Call Ratio | > 1.0 | < 0.7 | ±1 |

**判定**:
- スコア ≥ 3 → Risk On
- スコア ≤ -2 → Risk Off
- その他 → Neutral

---

## 完了条件

| # | 条件 | 確認方法 |
|---|------|----------|
| 1 | Market Status APIが動作 | `GET /api/market/status` が判定結果を返す |
| 2 | Indicators APIが動作 | `GET /api/market/indicators` が各指標を返す |
| 3 | ダッシュボードが表示される | `http://localhost:3000` で市場状態が表示 |
| 4 | 判定ロジックが正しく動作 | VIX 15, RSI 55 の時にRisk Onと判定される |

---

## 次のフェーズへ

Phase 2 完了後 → [Phase 3: Screener Module](./phase3-screener.md)
