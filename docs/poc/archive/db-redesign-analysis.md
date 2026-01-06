# DB設計見直し分析

## 目的

現在のDB設計の問題点を整理し、リファクタリング方針を決定する。

---

## 1. 現状のユースケース

### 1.1 Screener（銘柄スクリーニング）

| エンドポイント | 用途 | 使用テーブル |
|---------------|------|-------------|
| `GET /screener/canslim` | CAN-SLIM条件でフィルタリング | stocks, stock_prices, stock_metrics |
| `GET /screener/stock/{symbol}` | 個別銘柄詳細 | 同上 |

**フィルター条件:**
- min_rs_rating（デフォルト80）
- min_eps_growth_quarterly/annual（デフォルト25%）
- max_distance_from_52w_high（デフォルト15%）
- min_volume_ratio（デフォルト1.5）
- min_canslim_score（デフォルト70）

### 1.2 Market（市場環境）

| エンドポイント | 用途 | 使用テーブル |
|---------------|------|-------------|
| `GET /market/status` | Risk On/Off/Neutral判定 | market_snapshots, market_benchmarks |
| `GET /market/indicators` | VIX, S&P500, RSI等 | 同上 |

### 1.3 Portfolio（ポートフォリオ管理）

| エンドポイント | 用途 | 使用テーブル |
|---------------|------|-------------|
| Watchlist CRUD | 監視銘柄管理 | watchlist |
| Trades CRUD | ペーパートレード記録 | paper_trades |
| Performance | パフォーマンス計算 | paper_trades |

### 1.4 Data（株価データ）

| エンドポイント | 用途 | データ取得元 |
|---------------|------|-------------|
| `GET /data/quote/{symbol}` | 現在株価 | Yahoo Finance API（リアルタイム） |
| `GET /data/history/{symbol}` | 過去株価 | Yahoo Finance API + price_cache |
| `GET /data/financials/{symbol}` | 財務指標 | Yahoo Finance API |

### 1.5 Admin（管理）

| エンドポイント | 用途 | 使用テーブル |
|---------------|------|-------------|
| `POST /admin/screener/refresh` | データ更新ジョブ開始 | job_executions |

---

## 2. ジョブフロー

```
Job 0: CollectBenchmarksJob
  └─ market_benchmarks へ保存（S&P500, NASDAQ100のパフォーマンス）

Job 1: CollectStockDataJob
  └─ stocks へ保存（銘柄マスター）
  └─ stock_prices へ保存（日次価格）
  └─ stock_metrics へ保存（relative_strength のみ、rs_rating/canslim_scoreはNULL）

Job 2: CalculateRSRatingJob
  └─ stock_metrics.rs_rating を更新（パーセンタイル計算）

Job 3: CalculateCANSLIMJob
  └─ stock_metrics.canslim_score を更新
```

**実行順序の依存関係:**
- Job 0 → Job 1（ベンチマークデータがRS計算に必要）
- Job 1 → Job 2（relative_strengthがrs_rating計算に必要）
- Job 2 → Job 3（rs_ratingがcanslim_score計算に必要）

---

## 3. 現状のテーブル構造

### 3.1 正規化テーブル（新設計）

```
stocks (銘柄マスター)
├── symbol (PK)
├── name
├── industry
├── created_at
└── updated_at

stock_prices (日次価格スナップショット)
├── id (PK)
├── symbol (FK → stocks)
├── price
├── change_percent
├── volume
├── avg_volume_50d
├── market_cap
├── week_52_high
├── week_52_low
└── recorded_at

stock_metrics (計算指標)
├── id (PK)
├── symbol (FK → stocks)
├── eps_growth_quarterly
├── eps_growth_annual
├── institutional_ownership
├── relative_strength
├── rs_rating
├── canslim_score
└── calculated_at
```

### 3.2 非正規化テーブル（レガシー）

```
screener_results (1テーブルで完結)
├── symbol (PK)
├── name
├── price
├── change_percent
├── volume
├── avg_volume
├── market_cap
├── pe_ratio
├── week_52_high
├── week_52_low
├── eps_growth_quarterly
├── eps_growth_annual
├── rs_rating
├── institutional_ownership
├── canslim_total_score
├── canslim_detail (JSON)
└── updated_at
```

### 3.3 その他テーブル

| テーブル | 用途 | 状態 |
|---------|------|------|
| market_benchmarks | S&P500/NASDAQ100パフォーマンス | 使用中 |
| market_snapshots | マーケット状態 | 使用中 |
| watchlist | 監視銘柄 | 使用中 |
| paper_trades | ペーパートレード | 使用中 |
| price_cache | APIキャッシュ | 使用中 |
| job_executions | ジョブ履歴 | 使用中 |

---

## 4. 問題点

### 4.1 テーブル構造の重複

正規化テーブル（stocks + stock_prices + stock_metrics）と非正規化テーブル（screener_results）が並存している。

**影響:**
- どちらを信頼すべきか不明確
- データ同期の問題
- コードの複雑化

### 4.2 スクリーニングクエリの複雑さ

現在の `postgres_stock_query_repository.py` では:
```python
stmt = (
    select(StockModel, StockPriceModel, StockMetricsModel)
    .join(StockPriceModel, StockModel.symbol == StockPriceModel.symbol)
    .join(StockMetricsModel, StockModel.symbol == StockMetricsModel.symbol)
    .where(func.date(StockPriceModel.recorded_at) == today)
    .where(func.date(StockMetricsModel.calculated_at) == today)
    ...
)
```

**問題:**
- 3テーブルJOINが必要
- 当日データでのフィルタリングが複雑
- パフォーマンス懸念

### 4.3 日次スナップショット設計の是非

**現状:**
- stock_prices: 毎日新規INSERT
- stock_metrics: 毎日新規INSERT

**疑問点:**
- 履歴が本当に必要か？
- 「最新」を取得するために毎回ORDER BY + LIMITが必要

### 4.4 StockAggregate の使いにくさ

```python
StockAggregate: TypeAlias = tuple[StockIdentity, PriceSnapshot | None, StockMetrics | None]

# アクセスが不便
stock[0].symbol  # StockIdentity
stock[1].price   # PriceSnapshot
stock[2].rs_rating  # StockMetrics
```

---

## 5. 設計オプション

### Option A: 正規化設計で統一

**方針:**
- screener_results テーブルを削除
- stocks + stock_prices + stock_metrics を正式採用
- 履歴は保持（将来の分析用）

**メリット:**
- データの正規化が維持される
- 履歴データを活用可能
- 将来の拡張性

**デメリット:**
- JOINクエリが必要
- 最新データ取得が複雑

**必要な作業:**
- screener_results 参照コードの削除
- StockModelMapper の削除
- クエリ最適化（マテリアライズドビュー検討）

---

### Option B: 非正規化設計で統一

**方針:**
- stocks, stock_prices, stock_metrics を削除
- screener_results を正式採用（リネーム: stocks_current）
- 履歴が必要な場合は別テーブル（stocks_history）

**メリット:**
- クエリがシンプル（1テーブル）
- パフォーマンス良好
- 実装がシンプル

**デメリット:**
- データ重複
- 履歴管理が別途必要

**必要な作業:**
- 正規化テーブル削除
- ジョブの保存先変更
- ドメインモデル簡素化

---

### Option C: ハイブリッド設計

**方針:**
- stocks（マスター）は維持
- stock_prices + stock_metrics を統合 → stocks_daily
- screener_results は削除

```
stocks (マスター)
├── symbol (PK)
├── name
└── industry

stocks_daily (日次データ - 正規化テーブル統合)
├── symbol (PK, FK → stocks)
├── date (PK)
├── price, change_percent, volume, ...
├── eps_growth_quarterly, eps_growth_annual, ...
├── relative_strength, rs_rating, canslim_score
└── updated_at

stocks_current (最新データビュー or マテビュー)
└── stocks_daily の最新日のデータ
```

**メリット:**
- 履歴とカレントの両立
- マスターと日次データの分離
- クエリ最適化可能

**デメリット:**
- 移行作業が複雑

---

### Option D: UPSERT設計（履歴不要の場合）

**方針:**
- 履歴を保持しない
- 各テーブルは最新データのみ
- 毎日UPSERTで更新

```
stocks (マスター + 最新データ統合)
├── symbol (PK)
├── name
├── industry
├── price, change_percent, volume, ...
├── eps_growth_quarterly, eps_growth_annual, ...
├── relative_strength, rs_rating, canslim_score
└── updated_at
```

**メリット:**
- 最もシンプル
- JOINなし
- パフォーマンス最良

**デメリット:**
- 履歴が失われる
- 過去データ分析不可

---

## 6. 判断材料

### Q1: 履歴データは必要か？

| 用途 | 必要性 |
|------|--------|
| RS Rating推移の分析 | △（あれば便利） |
| CAN-SLIMスコア推移 | △（あれば便利） |
| バックテスト | ○（必要） |
| デバッグ | △（直近数日あれば十分） |

### Q2: パフォーマンス要件は？

| 条件 | 現状 |
|------|------|
| 対象銘柄数 | ~500（S&P500） |
| 同時接続数 | 個人利用（1-2） |
| レスポンス目標 | 特に制約なし |

### Q3: 将来の拡張予定は？

- 銘柄数の拡大（NASDAQ全体等）
- バックテスト機能
- アラート機能

---

## 7. 推奨案

### POC段階の推奨: Option D（UPSERT設計）

**理由:**
1. POCの目的はCAN-SLIMスクリーニングの検証
2. 履歴分析は優先度が低い
3. シンプルな設計で開発速度向上
4. 本番移行時に再設計可能

**移行ステップ:**
1. stocksテーブルを拡張（価格・指標カラム追加）
2. ジョブをUPSERT方式に変更
3. stock_prices, stock_metrics, screener_results を削除
4. ドメインモデル簡素化

---

### 本番向け推奨: Option C（ハイブリッド設計）

**理由:**
1. 履歴データの価値が高い
2. バックテスト機能に必要
3. マテリアライズドビューで性能確保

---

## 8. 次のアクション

- [ ] 履歴データの必要性を確認
- [ ] Option選択
- [ ] 詳細設計ドキュメント作成
- [ ] 移行計画策定
