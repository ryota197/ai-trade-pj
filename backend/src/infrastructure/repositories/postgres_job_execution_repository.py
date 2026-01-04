"""ジョブ実行 PostgreSQLリポジトリ実装"""

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from src.infrastructure.database.models.job_execution_model import JobExecutionModel
from src.jobs.lib.models import JobExecution, JobStatus
from src.jobs.lib.repositories import JobExecutionRepository


class PostgresJobExecutionRepository(JobExecutionRepository):
    """PostgreSQLを使用したジョブ実行リポジトリ"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, job: JobExecution) -> JobExecution:
        """ジョブを作成"""
        model = JobExecutionModel(
            flow_id=job.flow_id,
            job_name=job.job_name,
            status=job.status.value,
            started_at=job.started_at,
            completed_at=job.completed_at,
            result=job.result,
            error_message=job.error_message,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    def get(self, flow_id: str, job_name: str) -> JobExecution | None:
        """複合主キーでジョブを取得"""
        stmt = select(JobExecutionModel).where(
            and_(
                JobExecutionModel.flow_id == flow_id,
                JobExecutionModel.job_name == job_name,
            )
        )
        result = self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    def get_by_flow_id(self, flow_id: str) -> list[JobExecution]:
        """フローIDで全ジョブを取得"""
        stmt = (
            select(JobExecutionModel)
            .where(JobExecutionModel.flow_id == flow_id)
            .order_by(JobExecutionModel.job_name)
        )
        result = self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    def update(self, job: JobExecution) -> JobExecution:
        """ジョブを更新（flow_id, job_name で識別）"""
        stmt = select(JobExecutionModel).where(
            and_(
                JobExecutionModel.flow_id == job.flow_id,
                JobExecutionModel.job_name == job.job_name,
            )
        )
        result = self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            raise ValueError(f"Job not found: {job.flow_id}/{job.job_name}")

        model.status = job.status.value
        model.started_at = job.started_at
        model.completed_at = job.completed_at
        model.result = job.result
        model.error_message = job.error_message

        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    def _to_entity(self, model: JobExecutionModel) -> JobExecution:
        """モデルをエンティティに変換"""
        return JobExecution(
            flow_id=model.flow_id,
            job_name=model.job_name,
            status=JobStatus(model.status),
            started_at=model.started_at,
            completed_at=model.completed_at,
            result=model.result,
            error_message=model.error_message,
        )
