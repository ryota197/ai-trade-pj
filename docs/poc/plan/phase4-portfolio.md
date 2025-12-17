# Phase 4: Portfolio Module

## 目的

ウォッチリスト管理とペーパートレード記録機能を実装し、
投資判断の追跡とパフォーマンス検証を可能にする。

---

## ゴール

- ウォッチリストに銘柄を追加・削除できる
- ペーパートレード（仮想売買）を記録できる
- パフォーマンス（勝率、平均リターン等）が集計される

---

## タスク

### 4.1 Domain層実装

- [ ] `WatchlistItem` Entity作成
- [ ] `PaperTrade` Entity作成
- [ ] `PerformanceMetrics` Value Object作成
- [ ] `WatchlistRepository` Interface作成
- [ ] `TradeRepository` Interface作成
- [ ] `PerformanceCalculator` Domain Service作成

**成果物**:
```
backend/src/domain/
├── entities/
│   ├── watchlist_item.py
│   └── paper_trade.py
├── value_objects/
│   └── performance_metrics.py
├── services/
│   └── performance_calculator.py
└── repositories/
    ├── watchlist_repository.py
    └── trade_repository.py
```

---

### 4.2 Application層実装

- [ ] `ManageWatchlistUseCase` 作成（追加・削除・一覧取得）
- [ ] `RecordTradeUseCase` 作成
- [ ] `GetTradesUseCase` 作成
- [ ] `GetPerformanceUseCase` 作成
- [ ] 入出力DTO定義

**成果物**:
```
backend/src/application/
├── use_cases/
│   └── portfolio/
│       ├── manage_watchlist.py
│       ├── record_trade.py
│       ├── get_trades.py
│       └── get_performance.py
└── dto/
    └── portfolio_dto.py
```

---

### 4.3 Infrastructure層実装

- [ ] `WatchlistModel` SQLAlchemyモデル作成
- [ ] `PaperTradeModel` SQLAlchemyモデル作成
- [ ] `PostgresWatchlistRepository` 実装
- [ ] `PostgresTradeRepository` 実装

**成果物**:
```
backend/src/infrastructure/
├── repositories/
│   ├── postgres_watchlist_repository.py
│   └── postgres_trade_repository.py
└── database/
    └── models/
        ├── watchlist_model.py
        └── paper_trade_model.py
```

---

### 4.4 Presentation層実装

- [ ] `portfolio_controller.py` ルーター作成
- [ ] `GET /api/portfolio/watchlist` エンドポイント
- [ ] `POST /api/portfolio/watchlist` エンドポイント
- [ ] `DELETE /api/portfolio/watchlist/{symbol}` エンドポイント
- [ ] `GET /api/portfolio/trades` エンドポイント
- [ ] `POST /api/portfolio/trades` エンドポイント
- [ ] `GET /api/portfolio/performance` エンドポイント
- [ ] Pydanticスキーマ定義

**成果物**:
```
backend/src/presentation/
├── api/
│   └── portfolio_controller.py
└── schemas/
    └── portfolio.py
```

**API確認**:
```bash
# ウォッチリスト追加
curl -X POST http://localhost:8000/api/portfolio/watchlist \
  -H "Content-Type: application/json" \
  -d '{"symbol": "NVDA", "target_entry_price": 440.00}'

# トレード記録
curl -X POST http://localhost:8000/api/portfolio/trades \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "trade_type": "buy", "quantity": 10, "price": 180.00}'

# パフォーマンス取得
curl http://localhost:8000/api/portfolio/performance
# {"win_rate": 72.0, "average_return": 8.5, "total_trades": 25, ...}
```

---

### 4.5 Frontend - ポートフォリオUI

- [ ] `app/portfolio/page.tsx` ポートフォリオページ作成
- [ ] `WatchlistTable` コンポーネント作成
- [ ] `AddToWatchlistButton` コンポーネント作成
- [ ] `TradeHistory` コンポーネント作成
- [ ] `TradeForm` コンポーネント作成
- [ ] `PerformanceSummary` コンポーネント作成
- [ ] カスタムフック作成（`useWatchlist`, `useTrades`, `usePerformance`）

**成果物**:
```
frontend/src/
├── app/
│   └── portfolio/
│       └── page.tsx
├── components/
│   └── portfolio/
│       ├── WatchlistTable.tsx
│       ├── AddToWatchlistButton.tsx
│       ├── TradeHistory.tsx
│       ├── TradeForm.tsx
│       ├── PerformanceSummary.tsx
│       └── index.ts
├── hooks/
│   ├── useWatchlist.ts
│   ├── useTrades.ts
│   └── usePerformance.ts
└── types/
    └── portfolio.ts
```

**UI要素**:

#### ウォッチリスト
- 銘柄一覧（Symbol, 現在価格, 目標価格, ストップロス）
- 追加ボタン（モーダルでSymbol入力）
- 削除ボタン

#### トレード記録
- 売買履歴テーブル（日時, Symbol, 売買, 数量, 価格）
- 新規トレード入力フォーム

#### パフォーマンス
- 勝率（%）
- 平均リターン（%）
- 総トレード数
- 最大ドローダウン

---

## パフォーマンス計算ロジック

### 指標定義

| 指標 | 計算式 |
|------|--------|
| 勝率 | 勝ちトレード数 / 総トレード数 × 100 |
| 平均リターン | Σ(各トレードのリターン%) / 総トレード数 |
| プロフィットファクター | 総利益 / 総損失 |
| 最大ドローダウン | 期間中の最大資産減少率 |
| 平均保有日数 | Σ(保有日数) / 総トレード数 |

### トレードのリターン計算

```
リターン(%) = (売却価格 - 購入価格) / 購入価格 × 100
```

---

## 完了条件

| # | 条件 | 確認方法 |
|---|------|----------|
| 1 | ウォッチリスト追加ができる | POSTで銘柄追加、GETで確認 |
| 2 | ウォッチリスト削除ができる | DELETEで銘柄削除 |
| 3 | トレード記録ができる | POSTでトレード記録、GETで確認 |
| 4 | パフォーマンスが計算される | GETで勝率等が返る |
| 5 | ポートフォリオUIが表示 | `http://localhost:3000/portfolio` |

---

## PoC完了後

Phase 4 完了で PoC基本機能は完成。

### 検証項目
- [ ] CAN-SLIMスクリーニングの有効性
- [ ] マーケット状態判定の精度
- [ ] ペーパートレードでの勝率検証

### 次のステップ（検証結果次第）
- Phase 5: MLによるチャートパターン認識
- 本番環境へのデプロイ検討
- リアルタイムデータ対応
