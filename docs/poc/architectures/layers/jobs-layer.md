# Jobs層 実装ガイド

## 概要

Jobs層はバックグラウンドジョブの実行を担当する層。
長時間実行される処理、段階的計算、複数ジョブのオーケストレーションを行う。
Domain層のみに依存し、外部サービスはインターフェース経由で利用する。

---

## Application層との違い

| 観点 | Application (UseCase) | Jobs |
|------|----------------------|------|
| 実行方式 | 同期（リクエスト/レスポンス） | 非同期（バックグラウンド） |
| 実行時間 | 短時間（秒単位） | 長時間可（分〜時間） |
| 呼び出し元 | Controller | UseCase or スケジューラ |
| 進捗管理 | 不要 | 必要（DBで進捗追跡） |
| エラー影響 | リクエスト失敗 | 他銘柄の処理は継続 |
| 例 | GetStockDetail | CollectStockData |

---

## ディレクトリ構造

```
backend/src/jobs/
├── __init__.py
│
├── lib/                          # 共通基盤
│   ├── __init__.py
│   ├── base.py                   # Job 基底クラス
│   ├── state.py                  # ジョブ実行状態（進捗管理）
│   └── errors.py                 # ジョブ固有エラー
│
├── executions/                   # 個別ジョブ実装（単一責務）
│   ├── __init__.py
│   ├── collect_stock_data.py     # Job 1: データ収集
│   ├── calculate_rs_rating.py    # Job 2: RS Rating 計算
│   └── calculate_canslim.py      # Job 3: CAN-SLIM スコア計算
│
└── flows/                        # 複数ジョブのオーケストレーション
    ├── __init__.py
    └── refresh_screener.py       # データ更新フロー
```

---

## 構成要素

| 要素 | 責務 | 配置場所 |
|------|------|----------|
| Job 基底クラス | 共通インターフェース定義 | `jobs/lib/base.py` |
| Execution | 単一責務のジョブ実装 | `jobs/executions/` |
| Flow | 複数ジョブのオーケストレーション | `jobs/flows/` |
| JobState | ジョブ実行状態（進捗管理） | `jobs/lib/state.py` |
| Errors | ジョブ固有の例外 | `jobs/lib/errors.py` |

---

## コード例

### Job 基底クラス

```python
# jobs/lib/base.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")

class Job(ABC, Generic[TInput, TOutput]):
    """ジョブ基底クラス"""

    @property
    @abstractmethod
    def name(self) -> str:
        """ジョブ識別名"""
        pass

    @abstractmethod
    async def execute(self, input_: TInput) -> TOutput:
        """ジョブ実行"""
        pass
```

### Execution（個別ジョブ）

```python
# jobs/executions/collect_stock_data.py
from dataclasses import dataclass, field

from src.application.interfaces.financial_data_gateway import FinancialDataGateway
from src.domain.models.canslim_stock import CANSLIMStock
from src.domain.repositories.canslim_stock_repository import CANSLIMStockRepository
from src.domain.services.rs_calculator import RSCalculator
from src.jobs.lib.base import Job


@dataclass
class CollectInput:
    """データ収集ジョブ入力"""
    symbols: list[str]
    source: str  # "sp500" | "nasdaq100"


@dataclass
class CollectOutput:
    """データ収集ジョブ出力"""
    processed: int
    succeeded: int
    failed: int
    errors: list[dict] = field(default_factory=list)


class CollectStockDataJob(Job[CollectInput, CollectOutput]):
    """
    データ収集ジョブ (Job 1)

    外部APIから株価・財務データを取得し、DBに保存する。

    責務:
        - 株価データ取得（quote, history）
        - 財務データ取得（EPS, institutional ownership等）
        - canslim_stocks テーブルへのUPSERT

    注意:
        - rs_rating, canslim_score は計算しない（後続ジョブに委譲）
        - 各銘柄は独立して処理（1銘柄の失敗が他に影響しない）
    """

    name = "collect_stock_data"

    def __init__(
        self,
        stock_repository: CANSLIMStockRepository,
        financial_gateway: FinancialDataGateway,
        rs_calculator: RSCalculator | None = None,
    ) -> None:
        self._stock_repo = stock_repository
        self._gateway = financial_gateway
        self._rs_calculator = rs_calculator or RSCalculator()

    async def execute(self, input_: CollectInput) -> CollectOutput:
        succeeded = 0
        failed = 0
        errors: list[dict] = []

        for symbol in input_.symbols:
            try:
                await self._process_single_symbol(symbol)
                succeeded += 1
            except Exception as e:
                failed += 1
                errors.append({"symbol": symbol, "error": str(e)})

        return CollectOutput(
            processed=len(input_.symbols),
            succeeded=succeeded,
            failed=failed,
            errors=errors,
        )

    async def _process_single_symbol(self, symbol: str) -> None:
        # 株価・財務データ取得
        quote = await self._gateway.get_quote(symbol)
        financials = await self._gateway.get_financial_metrics(symbol)
        history = await self._gateway.get_price_history(symbol, period="1y")

        # relative_strength 計算
        relative_strength = self._rs_calculator.calculate(history)

        # CANSLIMStock を構築して保存
        stock = CANSLIMStock(
            symbol=symbol,
            date=date.today(),
            price=quote.price,
            # ... 他フィールド
            relative_strength=relative_strength,
            rs_rating=None,       # Job 2 で計算
            canslim_score=None,   # Job 3 で計算
        )
        self._stock_repo.save(stock)
```

```python
# jobs/executions/calculate_rs_rating.py
from dataclasses import dataclass, field

from src.domain.repositories.canslim_stock_repository import CANSLIMStockRepository
from src.domain.services.rs_calculator import RSCalculator
from src.jobs.lib.base import Job


@dataclass
class CalculateRSRatingOutput:
    """RS Rating 計算出力"""
    total_stocks: int
    updated_count: int
    errors: list[dict] = field(default_factory=list)


class CalculateRSRatingJob(Job[None, CalculateRSRatingOutput]):
    """
    RS Rating 計算ジョブ (Job 2)

    DB内の全銘柄の relative_strength からパーセンタイルランキングを計算し、
    rs_rating (1-99) を一括更新する。

    責務:
        - DB内の全銘柄の最新 relative_strength を取得
        - パーセンタイル計算
        - canslim_stocks.rs_rating を一括更新

    注意:
        - 外部API呼び出しなし
        - Job 1 完了後に実行
        - 500銘柄でも数秒で完了
    """

    name = "calculate_rs_rating"

    def __init__(
        self,
        stock_repository: CANSLIMStockRepository,
        rs_calculator: RSCalculator | None = None,
    ) -> None:
        self._stock_repo = stock_repository
        self._rs_calculator = rs_calculator or RSCalculator()

    async def execute(self, _: None = None) -> CalculateRSRatingOutput:
        # 1. relative_strength が設定済みの全銘柄を取得
        stocks = self._stock_repo.find_all_with_relative_strength(date.today())

        # 2. パーセンタイル計算
        all_rs = [s.relative_strength for s in stocks]
        rs_ratings = {}
        for stock in stocks:
            rs_rating = self._rs_calculator.calculate_percentile_rank(
                stock.relative_strength, all_rs
            )
            rs_ratings[stock.symbol] = rs_rating

        # 3. 一括更新
        self._stock_repo.update_rs_ratings(date.today(), rs_ratings)

        return CalculateRSRatingOutput(
            total_stocks=len(stocks),
            updated_count=len(rs_ratings),
        )
```

### Flow（オーケストレーション）

```python
# jobs/flows/refresh_screener.py
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from src.jobs.executions.collect_stock_data import CollectStockDataJob, CollectInput
from src.jobs.executions.calculate_rs_rating import CalculateRSRatingJob
from src.jobs.executions.calculate_canslim import CalculateCANSLIMJob


@dataclass
class RefreshScreenerInput:
    """フロー入力"""
    source: str  # "sp500" | "nasdaq100"
    symbols: list[str] = field(default_factory=list)


@dataclass
class FlowStepResult:
    """フローステップ結果"""
    job_name: str
    success: bool
    message: str
    data: dict | None = None


@dataclass
class FlowResult:
    """フロー実行結果"""
    job_id: str
    success: bool
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    steps: list[FlowStepResult] = field(default_factory=list)


class RefreshScreenerFlow:
    """
    スクリーナーデータ更新フロー

    実行順序:
      1. CollectStockDataJob   - 外部APIからデータ収集
      2. CalculateRSRatingJob  - パーセンタイル計算
      3. CalculateCANSLIMJob   - CAN-SLIMスコア計算
    """

    def __init__(
        self,
        collect_job: CollectStockDataJob,
        rs_rating_job: CalculateRSRatingJob,
        canslim_job: CalculateCANSLIMJob,
        symbol_provider: "SymbolProvider",
    ) -> None:
        self.collect_job = collect_job
        self.rs_rating_job = rs_rating_job
        self.canslim_job = canslim_job
        self.symbol_provider = symbol_provider

    async def run(self, input_: RefreshScreenerInput) -> FlowResult:
        """フロー実行"""
        job_id = str(uuid4())
        started_at = datetime.now(timezone.utc)
        steps: list[FlowStepResult] = []

        # シンボルリスト取得
        symbols = input_.symbols or await self.symbol_provider.get_symbols(input_.source)

        # Step 1: データ収集
        collect_result = await self.collect_job.execute(
            CollectInput(symbols=symbols, source=input_.source)
        )
        steps.append(FlowStepResult(
            job_name="collect_stock_data",
            success=True,
            message=f"Collected {collect_result.succeeded}/{collect_result.processed}",
        ))

        # Step 2: RS Rating 計算
        rs_result = await self.rs_rating_job.execute(None)
        steps.append(FlowStepResult(
            job_name="calculate_rs_rating",
            success=True,
            message=f"Updated {rs_result.updated_count} stocks",
        ))

        # Step 3: CAN-SLIM スコア計算
        canslim_result = await self.canslim_job.execute(None)
        steps.append(FlowStepResult(
            job_name="calculate_canslim",
            success=True,
            message=f"Updated {canslim_result.updated_count} stocks",
        ))

        completed_at = datetime.now(timezone.utc)
        return FlowResult(
            job_id=job_id,
            success=True,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=(completed_at - started_at).total_seconds(),
            steps=steps,
        )
```

---

## ジョブ一覧

| Job | 名前 | 責務 | 依存サービス |
|-----|------|------|-------------|
| Job 1 | `CollectStockDataJob` | 外部APIからデータ収集 | FinancialDataGateway, CANSLIMStockRepository |
| Job 2 | `CalculateRSRatingJob` | RS Rating パーセンタイル計算 | CANSLIMStockRepository, RSCalculator |
| Job 3 | `CalculateCANSLIMJob` | CAN-SLIM スコア計算 | CANSLIMStockRepository, CANSLIMScoreCalculator |

### ジョブ間の依存関係

```
Job 1: CollectStockData
  │
  │  更新フィールド:
  │    - price, volume, change_percent, ...
  │    - eps_growth_quarterly, eps_growth_annual, ...
  │    - relative_strength
  │
  ▼
Job 2: CalculateRSRating
  │
  │  更新フィールド:
  │    - rs_rating (1-99)
  │
  │  前提条件:
  │    - 全銘柄の relative_strength が設定済み
  │
  ▼
Job 3: CalculateCANSLIM
  │
  │  更新フィールド:
  │    - canslim_score (0-100)
  │    - score_c, score_a, score_n, score_s, score_l, score_i, score_m
  │
  │  前提条件:
  │    - rs_rating が設定済み
  ▼
完了
```

---

## 進捗管理

### refresh_jobs テーブル

ジョブの進捗状況はDBで管理する。

```sql
CREATE TABLE refresh_jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(50) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL,       -- pending, running, completed, failed, cancelled
    source VARCHAR(20) NOT NULL,
    total_symbols INTEGER NOT NULL,
    processed_count INTEGER NOT NULL,
    succeeded_count INTEGER NOT NULL,
    failed_count INTEGER NOT NULL,
    errors TEXT,                        -- JSON配列
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL
);
```

### 進捗更新タイミング

- ジョブ開始時: `status = "running"`, `started_at` 設定
- 10銘柄処理ごと: `processed_count`, `succeeded_count`, `failed_count` 更新
- ジョブ完了時: `status = "completed"`, `completed_at` 設定

---

## エラーハンドリング

### 原則

1. **銘柄単位で独立**: 1銘柄の失敗が他銘柄に影響しない
2. **エラー記録**: 失敗した銘柄とエラー内容をリストに記録
3. **処理継続**: 失敗してもスキップして次の銘柄へ
4. **ジョブ結果にエラー一覧を含める**

### コード例

```python
errors: list[dict] = []

for symbol in symbols:
    try:
        await self._process_single_symbol(symbol)
        succeeded += 1
    except Exception as e:
        failed += 1
        errors.append({"symbol": symbol, "error": str(e)})

return CollectOutput(
    processed=len(symbols),
    succeeded=succeeded,
    failed=failed,
    errors=errors,
)
```

---

## 呼び出し方法

### Application層から呼び出す場合

```python
# application/use_cases/admin/refresh_screener_data.py
class RefreshScreenerDataUseCase:
    def __init__(
        self,
        flow: RefreshScreenerFlow,
        job_repository: RefreshJobRepository,
    ):
        self._flow = flow
        self._job_repo = job_repository

    async def execute(self, input_: RefreshJobInput) -> RefreshJobOutput:
        # ジョブレコード作成
        job = await self._job_repo.create(...)

        # フロー実行（バックグラウンド）
        result = await self._flow.run(input_)

        return RefreshJobOutput(job_id=job.job_id, ...)
```

### Controller からバックグラウンド実行

```python
# presentation/api/admin_controller.py
@router.post("/screener/refresh")
async def start_refresh(
    request: RefreshJobRequest,
    background_tasks: BackgroundTasks,
    flow: RefreshScreenerFlow = Depends(get_refresh_screener_flow),
):
    # バックグラウンドタスクとして登録
    background_tasks.add_task(flow.run, input_)

    return ApiResponse(success=True, data={"status": "started"})
```

---

## 設計原則

1. **Domain層のみに依存**: Infrastructure層の実装に依存しない
2. **インターフェース経由**: 外部サービスは抽象インターフェースで定義
3. **単一責任**: 1ジョブ = 1責務
4. **段階的実行**: Job 1 → Job 2 → Job 3 の順に依存
5. **独立性**: 各銘柄の処理が他銘柄に影響しない
6. **再実行性**: 失敗時に該当ジョブのみ再実行可能

---

## 関連ドキュメント

- `docs/poc/plan/refresh-screener-usecase.md` - ジョブ設計詳細
- `docs/poc/plan/production-job-architecture.md` - 本番運用時のアーキテクチャ
- `docs/poc/architectures/layers/overview.md` - レイヤー設計概要
