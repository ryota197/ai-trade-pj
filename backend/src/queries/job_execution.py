"""ジョブ実行クエリ"""

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from src.models import JobExecution


class JobExecutionQuery:
    """ジョブ実行データアクセス"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, job: JobExecution) -> JobExecution:
        """ジョブを作成"""
        self._session.add(job)
        self._session.commit()
        self._session.refresh(job)
        return job

    def get(self, flow_id: str, job_name: str) -> JobExecution | None:
        """複合主キーでジョブを取得"""
        stmt = select(JobExecution).where(
            and_(
                JobExecution.flow_id == flow_id,
                JobExecution.job_name == job_name,
            )
        )
        return self._session.scalars(stmt).first()

    def get_by_flow_id(self, flow_id: str) -> list[JobExecution]:
        """フローIDで全ジョブを取得"""
        stmt = (
            select(JobExecution)
            .where(JobExecution.flow_id == flow_id)
            .order_by(JobExecution.job_name)
        )
        return list(self._session.scalars(stmt).all())

    def update(self, job: JobExecution) -> JobExecution:
        """ジョブを更新（flow_id, job_name で識別）"""
        existing = self.get(job.flow_id, job.job_name)

        if existing is None:
            raise ValueError(f"Job not found: {job.flow_id}/{job.job_name}")

        existing.status = job.status
        existing.started_at = job.started_at
        existing.completed_at = job.completed_at
        existing.result = job.result
        existing.error_message = job.error_message

        self._session.commit()
        self._session.refresh(existing)
        return existing
