"""マーケットデータ更新フロー"""

from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from src.models import FlowExecution, JobExecution
from src.queries import FlowExecutionQuery, JobExecutionQuery
from src.jobs.executions.collect_market_data import CollectMarketDataJob


@dataclass
class FlowResult:
    """フロー実行結果"""

    flow_id: str
    success: bool
    started_at: datetime
    completed_at: datetime
    duration_seconds: float


# ジョブ定義（1ジョブのみ）
JOB_DEFINITIONS = ["collect_market_data"]


class RefreshMarketFlow:
    """
    マーケットデータ更新フロー

    実行順序:
      1. collect_market_data - yfinanceからマーケット指標を収集

    進捗追跡:
      - flow_executions テーブルでフロー全体の状態を管理
      - job_executions テーブルで各ジョブの状態を管理
    """

    FLOW_NAME = "refresh_market"

    def __init__(
        self,
        collect_job: CollectMarketDataJob,
        flow_query: FlowExecutionQuery,
        job_query: JobExecutionQuery,
    ) -> None:
        self.collect_job = collect_job
        self._flow_query = flow_query
        self._job_query = job_query

    async def run(self) -> FlowResult:
        """
        フロー実行

        マーケット指標を取得してDBに保存する。
        """
        # フロー開始を記録
        flow = FlowExecution(
            flow_id=str(uuid4()),
            flow_name=self.FLOW_NAME,
            total_jobs=len(JOB_DEFINITIONS),
        )
        flow.start(first_job=JOB_DEFINITIONS[0])
        self._flow_query.create(flow)

        # ジョブレコードを作成
        job = JobExecution(
            flow_id=flow.flow_id,
            job_name="collect_market_data",
        )
        self._job_query.create(job)

        try:
            # ジョブ実行
            await self._execute_job(job, flow)

            # フロー完了
            flow.complete()
            self._flow_query.update(flow)

        except Exception:
            # フロー失敗を記録
            flow.fail()
            self._flow_query.update(flow)
            raise

        return FlowResult(
            flow_id=flow.flow_id,
            success=True,
            started_at=flow.started_at,
            completed_at=flow.completed_at,
            duration_seconds=flow.duration_seconds or 0,
        )

    async def _execute_job(
        self,
        job: JobExecution,
        flow: FlowExecution,
    ) -> None:
        """単一ジョブを実行し、状態を更新"""
        # ジョブ開始
        job.start()
        self._job_query.update(job)

        try:
            # ジョブ実行
            result = await self.collect_job.execute(None)

            # ジョブ完了
            job.complete(result=self._to_result_dict(result))
            self._job_query.update(job)

            # フロー進捗更新
            flow.advance(next_job=None)
            self._flow_query.update(flow)

        except Exception as e:
            # ジョブ失敗（result をクリアしてからDB更新）
            job.result = None
            job.fail(error_message=str(e))
            self._job_query.update(job)
            raise

    def _to_result_dict(self, result: Any) -> dict:
        """結果をdict に変換（enum も文字列化）"""
        try:
            return self._serialize_dataclass(result)
        except TypeError:
            return {"raw": str(result)}

    def _serialize_dataclass(self, obj: Any) -> Any:
        """dataclass を JSON シリアライズ可能な dict に変換"""
        if is_dataclass(obj) and not isinstance(obj, type):
            return {
                field.name: self._serialize_dataclass(getattr(obj, field.name))
                for field in fields(obj)
            }
        elif isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, list):
            return [self._serialize_dataclass(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: self._serialize_dataclass(v) for k, v in obj.items()}
        else:
            return obj
