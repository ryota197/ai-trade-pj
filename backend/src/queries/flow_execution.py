"""フロー実行クエリ"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import FlowExecution


class FlowExecutionQuery:
    """フロー実行データアクセス"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, flow: FlowExecution) -> FlowExecution:
        """フローを作成"""
        self._session.add(flow)
        self._session.commit()
        self._session.refresh(flow)
        return flow

    def get_by_id(self, flow_id: str) -> FlowExecution | None:
        """フローIDで取得"""
        stmt = select(FlowExecution).where(FlowExecution.flow_id == flow_id)
        return self._session.scalars(stmt).first()

    def update(self, flow: FlowExecution) -> FlowExecution:
        """フローを更新"""
        existing = self.get_by_id(flow.flow_id)

        if existing is None:
            raise ValueError(f"Flow not found: {flow.flow_id}")

        existing.status = flow.status
        existing.completed_jobs = flow.completed_jobs
        existing.current_job = flow.current_job
        existing.started_at = flow.started_at
        existing.completed_at = flow.completed_at

        self._session.commit()
        self._session.refresh(existing)
        return existing

    def get_latest(self, limit: int = 10) -> list[FlowExecution]:
        """最新のフローを取得"""
        stmt = (
            select(FlowExecution)
            .order_by(FlowExecution.created_at.desc())
            .limit(limit)
        )
        return list(self._session.scalars(stmt).all())
