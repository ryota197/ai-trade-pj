# スクリーニングデータ更新 設計書

## 概要

スクリーニングデータを更新するためのジョブ設計。
責務を明確に分離し、各ジョブが独立して実行可能な設計とする。

---

## 設計原則

1. **責務分離**: 1ジョブ = 1責務
2. **独立性**: 各銘柄の処理が他銘柄に影響しない
3. **再実行性**: 失敗時に該当ジョブのみ再実行可能
4. **正確性**: RS Ratingは常にDB全銘柄でパーセンタイル計算

---

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ジョブ分離アーキテクチャ                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  【Job 1】データ収集ジョブ (CollectStockDataJob)                         │
│    ─────────────────────────────────────────                            │
│    目的: 外部APIからデータを取得し、DBに保存                              │
│    特徴:                                                                │
│      - 各銘柄を独立して処理                                              │
│      - relative_strength を計算して保存                                  │
│      - rs_rating, canslim_score は計算しない（後続ジョブに委譲）          │
│    所要時間: 数分〜数十分（銘柄数・API速度に依存）                        │
│                                                                         │
│                              ↓ 完了後に自動実行                          │
│                                                                         │
│  【Job 2】RS Rating 再計算ジョブ (RecalculateRSRatingJob)                │
│    ─────────────────────────────────────────                            │
│    目的: DB内の全銘柄でパーセンタイルランキングを計算                      │
│    特徴:                                                                │
│      - 外部API呼び出しなし                                               │
│      - DB内の relative_strength を使用                                   │
│      - 全銘柄の rs_rating を一括更新                                     │
│    所要時間: 数秒                                                        │
│                                                                         │
│                              ↓ 完了後に自動実行                          │
│                                                                         │
│  【Job 3】CAN-SLIMスコア再計算ジョブ (RecalculateCANSLIMScoreJob)         │
│    ─────────────────────────────────────────                            │
│    目的: DB内のデータを元にCAN-SLIMスコアを計算                           │
│    特徴:                                                                │
│      - 外部API呼び出しなし                                               │
│      - rs_rating 確定後に実行                                            │
│      - 全銘柄の canslim_score を一括更新                                 │
│    所要時間: 数秒                                                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Job 1: データ収集ジョブ

### 責務

- 外部API (yfinance) からデータを取得
- `relative_strength` を計算
- DBに保存

### 入力

```python
@dataclass
class CollectStockDataInput:
    symbols: list[str]       # 対象銘柄リスト
    source: str              # "sp500" | "nasdaq100" | "custom"
```

### 処理フロー

```
1. ジョブ開始
   └─ ステータス: pending → running

2. S&P500 履歴取得（ベンチマーク）
   └─ sp500_prices: list[float]
   └─ benchmark_perf: PricePerformance

3. 銘柄ごとにデータ収集
   for symbol in symbols:
     ├─ get_quote(symbol)
     ├─ get_financial_metrics(symbol)
     ├─ get_price_history(symbol)
     ├─ calculate_relative_strength(stock_perf, benchmark_perf)
     ├─ DB保存 (rs_rating=NULL, canslim_score=NULL)
     └─ 進捗更新

4. ジョブ完了
   └─ ステータス: running → completed
   └─ 後続ジョブをトリガー (Job 2)
```

### 保存データ

| カラム | 値 |
|-------|-----|
| symbol | "AAPL" |
| price, volume, ... | APIから取得した値 |
| relative_strength | 計算値 (例: 105.2) |
| rs_rating | NULL (Job 2で計算) |
| canslim_score | NULL (Job 3で計算) |

### エラーハンドリング

- 銘柄ごとにtry-catch
- 失敗した銘柄はスキップし、エラーリストに記録
- 他銘柄の処理は継続

---

## Job 2: RS Rating 再計算ジョブ

### 責務

- DB内の全銘柄の `relative_strength` を取得
- パーセンタイルランキングを計算
- `rs_rating` を一括更新

### 入力

なし（DB全体を対象）

### 処理フロー

```
1. DB から全銘柄の relative_strength を取得
   SELECT symbol, relative_strength
   FROM stocks
   WHERE relative_strength IS NOT NULL

2. パーセンタイル計算
   sorted_rs = sorted(all_relative_strengths)
   for symbol, rs in stocks:
     rank = count(sorted_rs <= rs)
     percentile = (rank / total) * 100
     rs_rating = clamp(percentile, 1, 99)

3. 一括更新
   UPDATE stocks SET rs_rating = ? WHERE symbol = ?

4. 後続ジョブをトリガー (Job 3)
```

### パフォーマンス

- 外部API呼び出しなし
- 500銘柄でも数秒で完了

---

## Job 3: CAN-SLIMスコア再計算ジョブ

### 責務

- DB内のデータを元にCAN-SLIMスコアを計算
- `canslim_score` を一括更新

### 入力

なし（DB全体を対象）

### 処理フロー

```
1. DB から全銘柄のスコア計算に必要なデータを取得
   SELECT symbol, eps_growth_quarterly, eps_growth_annual,
          week_52_high, price, volume, avg_volume,
          rs_rating, institutional_ownership
   FROM stocks

2. 各銘柄のCAN-SLIMスコアを計算
   for stock in stocks:
     distance_from_high = (week_52_high - price) / week_52_high * 100
     volume_ratio = volume / avg_volume
     canslim_score = CANSLIMScore.calculate(
       eps_growth_quarterly,
       eps_growth_annual,
       distance_from_high,
       volume_ratio,
       rs_rating,
       institutional_ownership
     )

3. 一括更新
   UPDATE stocks SET canslim_score = ? WHERE symbol = ?
```

### パフォーマンス

- 外部API呼び出しなし
- 500銘柄でも数秒で完了

---

## DBスキーマ変更

### stocks テーブル

```sql
-- 追加カラム
ALTER TABLE stocks ADD COLUMN relative_strength DECIMAL(10, 4);

-- rs_rating, canslim_score は NULL 許容に変更
ALTER TABLE stocks ALTER COLUMN rs_rating DROP NOT NULL;
ALTER TABLE stocks ALTER COLUMN canslim_score DROP NOT NULL;
```

### 変更後のカラム一覧

| カラム | 型 | NULL | 説明 |
|-------|-----|------|------|
| relative_strength | DECIMAL(10,4) | YES | S&P500比の相対強度 |
| rs_rating | INTEGER | YES | パーセンタイルランク (1-99) |
| canslim_score | INTEGER | YES | CAN-SLIMスコア (0-100) |

---

## API設計

### 1. データ収集開始

```http
POST /api/admin/screener/refresh
Content-Type: application/json

{
  "symbols": ["AAPL", "NVDA", "MSFT"],  // または省略
  "source": "sp500"  // "sp500" | "nasdaq100" | "custom"
}
```

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "job_id": "collect_20240115_103000",
    "job_type": "collect_data",
    "status": "pending",
    "total_symbols": 500
  }
}
```

### 2. RS Rating 再計算のみ

```http
POST /api/admin/screener/recalculate
Content-Type: application/json

{
  "target": "rs_rating"  // "rs_rating" | "canslim_score" | "all"
}
```

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "job_id": "recalc_20240115_103000",
    "job_type": "recalculate_rs_rating",
    "status": "pending"
  }
}
```

### 3. ジョブステータス確認

```http
GET /api/admin/screener/jobs/{job_id}/status
```

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "job_id": "collect_20240115_103000",
    "job_type": "collect_data",
    "status": "running",
    "progress": {
      "total": 500,
      "processed": 250,
      "succeeded": 245,
      "failed": 5,
      "percentage": 50.0
    },
    "timing": {
      "started_at": "2024-01-15T10:30:00Z",
      "elapsed_seconds": 120,
      "estimated_remaining_seconds": 120
    },
    "errors": [
      {"symbol": "XYZ", "error": "Invalid symbol"}
    ],
    "next_job": "recalculate_rs_rating"  // 後続ジョブ
  }
}
```

---

## 実行パターン

### パターン A: フル更新（推奨）

```
管理者: POST /admin/screener/refresh { source: "sp500" }

実行順序:
  1. Job 1: データ収集 (500銘柄) - 数十分
  2. Job 2: RS Rating 再計算 - 数秒 (自動実行)
  3. Job 3: CAN-SLIMスコア再計算 - 数秒 (自動実行)
```

### パターン B: 1銘柄のみ更新

```
管理者: POST /admin/screener/refresh { symbols: ["AAPL"] }

実行順序:
  1. Job 1: データ収集 (1銘柄) - 数秒
  2. Job 2: RS Rating 再計算 (全500銘柄) - 数秒 (自動実行)
     └─ AAPL の relative_strength が他499銘柄と比較される
  3. Job 3: CAN-SLIMスコア再計算 (全500銘柄) - 数秒 (自動実行)
```

### パターン C: 再計算のみ

```
管理者: POST /admin/screener/recalculate { target: "all" }

実行順序:
  1. Job 2: RS Rating 再計算 - 数秒
  2. Job 3: CAN-SLIMスコア再計算 - 数秒 (自動実行)

※ データ収集なし。DB内の既存データで再計算。
```

---

## ジョブ状態遷移

```
                    ┌──────────┐
                    │ pending  │
                    └────┬─────┘
                         │ start
                         ▼
                    ┌──────────┐
         ┌──────────│ running  │──────────┐
         │          └────┬─────┘          │
         │ cancel        │ complete       │ error
         ▼               ▼                ▼
    ┌──────────┐   ┌──────────┐    ┌──────────┐
    │cancelled │   │completed │    │  failed  │
    └──────────┘   └────┬─────┘    └──────────┘
                        │
                        │ trigger next job
                        ▼
                   (次のジョブへ)
```

---

## ジョブチェーン

```python
class JobChain:
    """ジョブの連鎖実行を管理"""

    CHAINS = {
        "collect_data": ["recalculate_rs_rating", "recalculate_canslim_score"],
        "recalculate_rs_rating": ["recalculate_canslim_score"],
        "recalculate_canslim_score": [],
    }

    @classmethod
    def get_next_jobs(cls, job_type: str) -> list[str]:
        return cls.CHAINS.get(job_type, [])
```

---

## 実装タスク

### Phase 1: DBスキーマ変更

- [ ] `stocks` テーブルに `relative_strength` カラム追加
- [ ] `rs_rating`, `canslim_score` を NULL 許容に変更

### Phase 2: Job 1 (データ収集) リファクタリング

- [ ] `CollectStockDataUseCase` 作成
- [ ] `relative_strength` を計算して保存
- [ ] `rs_rating`, `canslim_score` は NULL のまま

### Phase 3: Job 2, 3 (再計算) 新規作成

- [ ] `RecalculateRSRatingUseCase` 作成
- [ ] `RecalculateCANSLIMScoreUseCase` 作成
- [ ] ジョブチェーン実装

### Phase 4: API更新

- [ ] `/admin/screener/recalculate` エンドポイント追加
- [ ] ジョブタイプに応じた処理分岐

### Phase 5: フロントエンド更新

- [ ] ジョブチェーンの進捗表示
- [ ] 再計算ボタン追加

---

## 成果物

```
backend/src/
├── application/
│   └── use_cases/
│       └── admin/
│           ├── collect_stock_data.py      # Job 1
│           ├── recalculate_rs_rating.py   # Job 2
│           └── recalculate_canslim_score.py  # Job 3
├── domain/
│   └── services/
│       └── job_chain.py                   # ジョブチェーン管理
└── presentation/
    └── api/
        └── admin_controller.py            # 更新
```

---

## 備考

- Job 2, 3 は高速なため、フロントエンドでは「処理中」の表示のみで十分
- 将来的にはJob 1を複数ワーカーで並列実行可能
- Celery/ARQ導入時もジョブ単位で移行しやすい設計
