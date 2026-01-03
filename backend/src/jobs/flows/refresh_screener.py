"""スクリーナーデータ更新フロー"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from src.jobs.executions.collect_stock_data import (
    CollectInput,
    CollectStockDataJob,
)
from src.jobs.executions.calculate_rs_rating import (
    CalculateRSRatingInput,
    CalculateRSRatingJob,
)


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

    def to_dict(self) -> dict:
        """辞書に変換（job_executions.result用）"""
        return {
            "steps": [
                {
                    "job_name": step.job_name,
                    "success": step.success,
                    "message": step.message,
                    "data": step.data,
                }
                for step in self.steps
            ],
        }


class RefreshScreenerFlow:
    """
    スクリーナーデータ更新フロー

    実行順序:
      1. collect_stock_data    - 外部APIからデータ収集
      2. calculate_rs_rating   - RS Ratingパーセンタイル計算
      3. calculate_canslim     - CAN-SLIMスコア計算（Phase 3で追加予定）
    """

    def __init__(
        self,
        collect_job: CollectStockDataJob,
        rs_rating_job: CalculateRSRatingJob,
        symbol_provider: "SymbolProvider",
    ) -> None:
        self.collect_job = collect_job
        self.rs_rating_job = rs_rating_job
        self.symbol_provider = symbol_provider

    async def run(self, input_: RefreshScreenerInput) -> FlowResult:
        """フロー実行"""
        job_id = str(uuid4())
        started_at = datetime.now(timezone.utc)
        steps: list[FlowStepResult] = []

        # シンボルリスト取得
        if input_.symbols:
            symbols = input_.symbols
        else:
            symbols = await self.symbol_provider.get_symbols(input_.source)

        # Step 1: データ収集
        collect_result = await self.collect_job.execute(
            CollectInput(symbols=symbols, source=input_.source)
        )
        steps.append(
            FlowStepResult(
                job_name=self.collect_job.name,
                success=True,
                message=f"Collected {collect_result.succeeded}/{collect_result.processed} symbols",
                data={
                    "succeeded": collect_result.succeeded,
                    "failed": collect_result.failed,
                    "errors": collect_result.errors[:10],  # 最大10件のみ
                },
            )
        )

        # Step 2: RS Rating再計算
        rs_result = await self.rs_rating_job.execute(
            CalculateRSRatingInput(target_date=None)  # 当日
        )
        steps.append(
            FlowStepResult(
                job_name=self.rs_rating_job.name,
                success=True,
                message=f"Updated RS Rating for {rs_result.updated_count}/{rs_result.total_stocks} stocks",
                data={
                    "total_stocks": rs_result.total_stocks,
                    "updated_count": rs_result.updated_count,
                    "errors": rs_result.errors[:10],
                },
            )
        )

        # TODO: Phase 3 で Job 3 を追加
        # Step 3: CAN-SLIMスコア再計算

        completed_at = datetime.now(timezone.utc)
        duration = (completed_at - started_at).total_seconds()

        return FlowResult(
            job_id=job_id,
            success=True,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration,
            steps=steps,
        )


class SymbolProvider:
    """
    シンボルプロバイダー（インターフェース）

    S&P500やNASDAQ100のシンボルリストを取得する。
    """

    async def get_symbols(self, source: str) -> list[str]:
        """
        シンボルリストを取得

        Args:
            source: "sp500" | "nasdaq100"

        Returns:
            list[str]: シンボルリスト
        """
        raise NotImplementedError()
