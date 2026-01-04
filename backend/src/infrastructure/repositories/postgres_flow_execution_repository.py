"""フロー実行 PostgreSQLリポジトリ実装"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.infrastructure.database.models.flow_execution_model import FlowExecutionModel
from src.jobs.lib.models import FlowExecution, FlowStatus
from src.jobs.lib.repositories import FlowExecutionRepository


class PostgresFlowExecutionRepository(FlowExecutionRepository):
    """PostgreSQLを使用したフロー実行リポジトリ"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, flow: FlowExecution) -> FlowExecution:
        """フローを作成"""
        model = FlowExecutionModel(
            flow_id=flow.flow_id,
            flow_name=flow.flow_name,
            status=flow.status.value,
            total_jobs=flow.total_jobs,
            completed_jobs=flow.completed_jobs,
            current_job=flow.current_job,
            started_at=flow.started_at,
            completed_at=flow.completed_at,
            created_at=flow.created_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    def get_by_id(self, flow_id: str) -> FlowExecution | None:
        """フローIDで取得"""
        stmt = select(FlowExecutionModel).where(
            FlowExecutionModel.flow_id == flow_id
        )
        result = self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    def update(self, flow: FlowExecution) -> FlowExecution:
        """フローを更新"""
        stmt = select(FlowExecutionModel).where(
            FlowExecutionModel.flow_id == flow.flow_id
        )
        result = self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            raise ValueError(f"Flow not found: {flow.flow_id}")

        model.status = flow.status.value
        model.completed_jobs = flow.completed_jobs
        model.current_job = flow.current_job
        model.started_at = flow.started_at
        model.completed_at = flow.completed_at

        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    def get_latest(self, limit: int = 10) -> list[FlowExecution]:
        """最新のフローを取得"""
        stmt = (
            select(FlowExecutionModel)
            .order_by(FlowExecutionModel.created_at.desc())
            .limit(limit)
        )
        result = self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    def _to_entity(self, model: FlowExecutionModel) -> FlowExecution:
        """モデルをエンティティに変換"""
        return FlowExecution(
            flow_id=model.flow_id,
            flow_name=model.flow_name,
            status=FlowStatus(model.status),
            total_jobs=model.total_jobs,
            completed_jobs=model.completed_jobs,
            current_job=model.current_job,
            started_at=model.started_at,
            completed_at=model.completed_at,
            created_at=model.created_at,
        )
