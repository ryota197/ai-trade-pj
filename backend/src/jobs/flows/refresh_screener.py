"""スクリーナーデータ更新フロー"""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any
from uuid import uuid4

from src.jobs.executions.collect_stock_data import (
    CollectInput,
    CollectStockDataJob,
)
from src.jobs.executions.calculate_rs_rating import (
    CalculateRSRatingInput,
    CalculateRSRatingJob,
)
from src.jobs.executions.calculate_canslim import (
    CalculateCANSLIMInput,
    CalculateCANSLIMJob,
)
from src.jobs.lib import (
    FlowExecution,
    JobExecution,
    FlowExecutionRepository,
    JobExecutionRepository,
)

# PoC実装での固定値
DEFAULT_SOURCE = "sp500"


@dataclass
class FlowResult:
    """フロー実行結果"""

    flow_id: str
    success: bool
    started_at: datetime
    completed_at: datetime
    duration_seconds: float


# ジョブ定義（順序付き）
JOB_DEFINITIONS = [
    "collect_stock_data",
    "calculate_rs_rating",
    "calculate_canslim",
]


class RefreshScreenerFlow:
    """
    スクリーナーデータ更新フロー

    実行順序:
      1. collect_stock_data    - 外部APIからデータ収集
      2. calculate_rs_rating   - RS Ratingパーセンタイル計算
      3. calculate_canslim     - CAN-SLIMスコア計算

    進捗追跡:
      - flow_executions テーブルでフロー全体の状態を管理
      - job_executions テーブルで各ジョブの状態を管理
    """

    FLOW_NAME = "refresh_screener"

    def __init__(
        self,
        collect_job: CollectStockDataJob,
        rs_rating_job: CalculateRSRatingJob,
        canslim_job: CalculateCANSLIMJob,
        symbol_provider: "SymbolProvider",
        flow_repository: FlowExecutionRepository,
        job_repository: JobExecutionRepository,
    ) -> None:
        self.collect_job = collect_job
        self.rs_rating_job = rs_rating_job
        self.canslim_job = canslim_job
        self.symbol_provider = symbol_provider
        self._flow_repo = flow_repository
        self._job_repo = job_repository

    async def run(self) -> FlowResult:
        """
        フロー実行

        S&P 500銘柄のスクリーニングデータを更新する。
        """
        # フロー開始を記録
        flow = FlowExecution(
            flow_id=str(uuid4()),
            flow_name=self.FLOW_NAME,
            total_jobs=len(JOB_DEFINITIONS),
        )
        flow.start(first_job=JOB_DEFINITIONS[0])
        self._flow_repo.create(flow)

        # 各ジョブのレコードを事前作成
        jobs = self._create_job_records(flow.flow_id)

        try:
            # S&P 500銘柄リストを取得
            symbols = await self.symbol_provider.get_symbols(DEFAULT_SOURCE)

            # Job 1: データ収集
            await self._execute_job(
                job=jobs[0],
                flow=flow,
                next_job=JOB_DEFINITIONS[1],
                execute_fn=lambda: self.collect_job.execute(
                    CollectInput(symbols=symbols, source=DEFAULT_SOURCE)
                ),
            )

            # Job 2: RS Rating再計算
            await self._execute_job(
                job=jobs[1],
                flow=flow,
                next_job=JOB_DEFINITIONS[2],
                execute_fn=lambda: self.rs_rating_job.execute(
                    CalculateRSRatingInput(target_date=None)
                ),
            )

            # Job 3: CAN-SLIMスコア再計算
            await self._execute_job(
                job=jobs[2],
                flow=flow,
                next_job=None,
                execute_fn=lambda: self.canslim_job.execute(
                    CalculateCANSLIMInput(target_date=None)
                ),
            )

            # フロー完了
            flow.complete()
            self._flow_repo.update(flow)

        except Exception:
            # フロー失敗を記録
            flow.fail()
            self._flow_repo.update(flow)
            raise

        return FlowResult(
            flow_id=flow.flow_id,
            success=True,
            started_at=flow.started_at,
            completed_at=flow.completed_at,
            duration_seconds=flow.duration_seconds or 0,
        )

    def _create_job_records(self, flow_id: str) -> list[JobExecution]:
        """ジョブレコードを事前作成"""
        jobs = []
        for job_name in JOB_DEFINITIONS:
            job = JobExecution(
                flow_id=flow_id,
                job_name=job_name,
            )
            self._job_repo.create(job)
            jobs.append(job)
        return jobs

    async def _execute_job(
        self,
        job: JobExecution,
        flow: FlowExecution,
        next_job: str | None,
        execute_fn: Any,
    ) -> None:
        """単一ジョブを実行し、状態を更新"""
        # ジョブ開始
        job.start()
        self._job_repo.update(job)

        try:
            # ジョブ実行
            result = await execute_fn()

            # ジョブ完了
            job.complete(result=self._to_result_dict(result))
            self._job_repo.update(job)

            # フロー進捗更新
            flow.advance(next_job=next_job)
            self._flow_repo.update(flow)

        except Exception as e:
            # ジョブ失敗
            job.fail(error_message=str(e))
            self._job_repo.update(job)
            raise

    def _to_result_dict(self, result: Any) -> dict:
        """結果をdict に変換"""
        try:
            return asdict(result)
        except TypeError:
            return {"raw": str(result)}


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
