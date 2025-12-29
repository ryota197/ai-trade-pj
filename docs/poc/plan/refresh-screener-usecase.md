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

## ジョブディレクトリ構造

```
backend/src/jobs/
├── lib/                              # 共有ユーティリティ
│   ├── __init__.py
│   ├── base.py                       # ジョブ基底クラス
│   ├── context.py                    # 実行コンテキスト
│   └── errors.py                     # ジョブ固有エラー
│
├── executions/                       # 個別ジョブ実装（単一責務）
│   ├── __init__.py
│   ├── collect_stock_data.py         # Job 1: データ収集
│   ├── recalculate_rs_rating.py      # Job 2: RS Rating再計算
│   └── recalculate_canslim.py        # Job 3: CAN-SLIMスコア再計算
│
└── flows/                            # 複数ジョブのオーケストレーション
    ├── __init__.py
    └── refresh_screener.py           # 収集 → RS → CAN-SLIM フロー
```

### 層の責務

| 層 | 責務 | 依存関係 |
|---|------|---------|
| `lib/` | 共通基盤（基底クラス、エラー、コンテキスト） | なし |
| `executions/` | 単一ジョブ実行（1ジョブ = 1ファイル） | `lib/` のみ |
| `flows/` | ジョブの組み合わせ・順序制御 | `executions/` |

---

## lib/ 設計

### base.py - ジョブ基底クラス

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar, Generic

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


@dataclass
class JobResult:
    """ジョブ実行結果"""
    success: bool
    message: str
    data: dict | None = None


class Job(ABC, Generic[TInput, TOutput]):
    """ジョブ基底クラス"""

    @property
    @abstractmethod
    def name(self) -> str:
        """ジョブ識別名"""
        pass

    @abstractmethod
    async def execute(self, input: TInput) -> TOutput:
        """ジョブ実行（サブクラスで実装）"""
        pass
```

### context.py - 実行コンテキスト

```python
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class JobContext:
    """ジョブ実行コンテキスト"""
    job_id: str
    started_at: datetime = field(default_factory=datetime.utcnow)

    # 進捗管理（オプション）
    total: int = 0
    processed: int = 0

    def update_progress(self, processed: int) -> None:
        self.processed = processed
```

### errors.py - ジョブ固有エラー

```python
class JobError(Exception):
    """ジョブ実行エラー基底クラス"""
    pass


class JobExecutionError(JobError):
    """ジョブ実行中のエラー"""
    def __init__(self, job_name: str, message: str):
        self.job_name = job_name
        super().__init__(f"[{job_name}] {message}")


class JobSkippedError(JobError):
    """ジョブがスキップされた"""
    pass
```

---

## executions/ 設計

### collect_stock_data.py

```python
from dataclasses import dataclass
from jobs.lib.base import Job


@dataclass
class CollectInput:
    symbols: list[str]
    source: str  # "sp500" | "nasdaq100"


@dataclass
class CollectOutput:
    processed: int
    succeeded: int
    failed: int
    errors: list[dict]


class CollectStockDataJob(Job[CollectInput, CollectOutput]):
    """データ収集ジョブ"""

    name = "collect_stock_data"

    def __init__(self, stock_repository, market_data_service):
        self.stock_repository = stock_repository
        self.market_data_service = market_data_service

    async def execute(self, input: CollectInput) -> CollectOutput:
        succeeded = 0
        failed = 0
        errors = []

        # ベンチマーク取得
        benchmark = await self.market_data_service.get_sp500_performance()

        for symbol in input.symbols:
            try:
                # データ取得
                quote = await self.market_data_service.get_quote(symbol)
                financials = await self.market_data_service.get_financials(symbol)
                history = await self.market_data_service.get_history(symbol)

                # relative_strength 計算
                stock_perf = self._calculate_performance(history)
                relative_strength = stock_perf / benchmark * 100

                # DB保存（rs_rating, canslim_score は NULL）
                await self.stock_repository.upsert(
                    symbol=symbol,
                    quote=quote,
                    financials=financials,
                    relative_strength=relative_strength,
                    rs_rating=None,
                    canslim_score=None,
                )
                succeeded += 1

            except Exception as e:
                failed += 1
                errors.append({"symbol": symbol, "error": str(e)})

        return CollectOutput(
            processed=len(input.symbols),
            succeeded=succeeded,
            failed=failed,
            errors=errors,
        )
```

### recalculate_rs_rating.py

```python
from dataclasses import dataclass
from jobs.lib.base import Job


@dataclass
class RSRatingOutput:
    updated_count: int


class RecalculateRSRatingJob(Job[None, RSRatingOutput]):
    """RS Rating再計算ジョブ"""

    name = "recalculate_rs_rating"

    def __init__(self, stock_repository):
        self.stock_repository = stock_repository

    async def execute(self, input: None = None) -> RSRatingOutput:
        # 全銘柄の relative_strength を取得
        stocks = await self.stock_repository.get_all_with_relative_strength()

        # パーセンタイル計算
        sorted_rs = sorted([s.relative_strength for s in stocks])
        total = len(sorted_rs)

        updates = []
        for stock in stocks:
            rank = sum(1 for rs in sorted_rs if rs <= stock.relative_strength)
            percentile = (rank / total) * 100
            rs_rating = max(1, min(99, int(percentile)))
            updates.append((stock.symbol, rs_rating))

        # 一括更新
        await self.stock_repository.bulk_update_rs_rating(updates)

        return RSRatingOutput(updated_count=len(updates))
```

### recalculate_canslim.py

```python
from dataclasses import dataclass
from jobs.lib.base import Job


@dataclass
class CANSLIMOutput:
    updated_count: int


class RecalculateCANSLIMJob(Job[None, CANSLIMOutput]):
    """CAN-SLIMスコア再計算ジョブ"""

    name = "recalculate_canslim"

    def __init__(self, stock_repository, canslim_calculator):
        self.stock_repository = stock_repository
        self.canslim_calculator = canslim_calculator

    async def execute(self, input: None = None) -> CANSLIMOutput:
        # 全銘柄のデータを取得
        stocks = await self.stock_repository.get_all_for_canslim()

        updates = []
        for stock in stocks:
            score = self.canslim_calculator.calculate(
                eps_growth_quarterly=stock.eps_growth_quarterly,
                eps_growth_annual=stock.eps_growth_annual,
                distance_from_high=stock.distance_from_52w_high,
                volume_ratio=stock.volume_ratio,
                rs_rating=stock.rs_rating,
                institutional_ownership=stock.institutional_ownership,
            )
            updates.append((stock.symbol, score))

        # 一括更新
        await self.stock_repository.bulk_update_canslim_score(updates)

        return CANSLIMOutput(updated_count=len(updates))
```

---

## flows/ 設計

### refresh_screener.py

```python
from dataclasses import dataclass
from jobs.executions.collect_stock_data import CollectStockDataJob, CollectInput
from jobs.executions.recalculate_rs_rating import RecalculateRSRatingJob
from jobs.executions.recalculate_canslim import RecalculateCANSLIMJob


@dataclass
class RefreshScreenerInput:
    source: str  # "sp500" | "nasdaq100"


@dataclass
class FlowStepResult:
    job_name: str
    success: bool
    message: str
    data: dict | None = None


@dataclass
class FlowResult:
    success: bool
    steps: list[FlowStepResult]


class RefreshScreenerFlow:
    """
    スクリーナーデータ更新フロー

    実行順序:
      1. collect_stock_data   - 外部APIからデータ収集
      2. recalculate_rs_rating - パーセンタイル計算
      3. recalculate_canslim   - CAN-SLIMスコア計算
    """

    def __init__(
        self,
        collect_job: CollectStockDataJob,
        rs_rating_job: RecalculateRSRatingJob,
        canslim_job: RecalculateCANSLIMJob,
        symbol_provider,  # S&P500/NASDAQ100のシンボル取得
    ):
        self.collect_job = collect_job
        self.rs_rating_job = rs_rating_job
        self.canslim_job = canslim_job
        self.symbol_provider = symbol_provider

    async def run(self, input: RefreshScreenerInput) -> FlowResult:
        """フロー実行"""
        steps = []

        # Step 1: データ収集
        symbols = await self.symbol_provider.get_symbols(input.source)
        collect_result = await self.collect_job.execute(
            CollectInput(symbols=symbols, source=input.source)
        )
        steps.append(FlowStepResult(
            job_name=self.collect_job.name,
            success=True,
            message=f"Collected {collect_result.succeeded}/{collect_result.processed} symbols",
            data={
                "succeeded": collect_result.succeeded,
                "failed": collect_result.failed,
                "errors": collect_result.errors,
            },
        ))

        # Step 2: RS Rating再計算
        rs_result = await self.rs_rating_job.execute()
        steps.append(FlowStepResult(
            job_name=self.rs_rating_job.name,
            success=True,
            message=f"Updated RS Rating for {rs_result.updated_count} symbols",
            data={"updated_count": rs_result.updated_count},
        ))

        # Step 3: CAN-SLIMスコア再計算
        canslim_result = await self.canslim_job.execute()
        steps.append(FlowStepResult(
            job_name=self.canslim_job.name,
            success=True,
            message=f"Updated CAN-SLIM score for {canslim_result.updated_count} symbols",
            data={"updated_count": canslim_result.updated_count},
        ))

        return FlowResult(success=True, steps=steps)
```

---

## Controller からの呼び出し

```python
# presentation/api/admin_controller.py

from jobs.flows.refresh_screener import RefreshScreenerFlow, RefreshScreenerInput


class AdminController:
    def __init__(self, refresh_flow: RefreshScreenerFlow):
        self.refresh_flow = refresh_flow

    async def start_refresh(self, source: str) -> dict:
        """スクリーナーデータ更新開始"""
        # BackgroundTasksで実行
        background_tasks.add_task(
            self._run_refresh_flow,
            RefreshScreenerInput(source=source)
        )
        return {"status": "started", "source": source}

    async def _run_refresh_flow(self, input: RefreshScreenerInput):
        result = await self.refresh_flow.run(input)
        # ログ出力など
        logger.info(f"Refresh flow completed: {result}")
```

---

## 成果物まとめ

```
backend/src/
├── jobs/                             # ジョブ専用ディレクトリ
│   ├── lib/
│   │   ├── base.py                   # Job 基底クラス
│   │   ├── context.py                # 実行コンテキスト
│   │   └── errors.py                 # エラー定義
│   ├── executions/
│   │   ├── collect_stock_data.py     # Job 1
│   │   ├── recalculate_rs_rating.py  # Job 2
│   │   └── recalculate_canslim.py    # Job 3
│   └── flows/
│       └── refresh_screener.py       # フロー定義
│
└── presentation/
    └── api/
        └── admin_controller.py       # API エンドポイント
```

---

## 備考

- Job 2, 3 は高速なため、フロントエンドでは「処理中」の表示のみで十分
- 将来的にはJob 1を複数ワーカーで並列実行可能
- Celery/ARQ導入時もジョブ単位で移行しやすい設計
- `flows/` は将来的に他のフローも追加可能（例: `daily_market_update.py`）
