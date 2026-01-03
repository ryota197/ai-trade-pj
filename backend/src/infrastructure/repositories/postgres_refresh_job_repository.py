"""リフレッシュジョブ PostgreSQLリポジトリ実装"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.infrastructure.database.models.refresh_job_model import RefreshJobModel


@dataclass
class RefreshJob:
    """リフレッシュジョブ（エンティティ）"""

    job_id: str
    status: str  # pending, running, completed, failed
    source: str
    total_symbols: int = 0
    processed_count: int = 0
    succeeded_count: int = 0
    failed_count: int = 0
    errors: list[str] | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class RefreshJobRepository(ABC):
    """リフレッシュジョブリポジトリインターフェース"""

    @abstractmethod
    async def create(self, job: RefreshJob) -> RefreshJob:
        """ジョブを作成"""
        pass

    @abstractmethod
    async def get_by_id(self, job_id: str) -> RefreshJob | None:
        """ジョブIDで取得"""
        pass

    @abstractmethod
    async def update(self, job: RefreshJob) -> RefreshJob:
        """ジョブを更新"""
        pass

    @abstractmethod
    async def get_latest(self, limit: int = 10) -> list[RefreshJob]:
        """最新のジョブを取得"""
        pass


class PostgresRefreshJobRepository(RefreshJobRepository):
    """PostgreSQLを使用したリフレッシュジョブリポジトリ"""

    def __init__(self, session: Session) -> None:
        self._session = session

    async def create(self, job: RefreshJob) -> RefreshJob:
        """ジョブを作成"""
        model = RefreshJobModel(
            job_id=job.job_id,
            status=job.status,
            source=job.source,
            total_symbols=job.total_symbols,
            processed_count=job.processed_count,
            succeeded_count=job.succeeded_count,
            failed_count=job.failed_count,
            errors=json.dumps(job.errors) if job.errors else None,
            started_at=job.started_at,
            completed_at=job.completed_at,
            created_at=job.created_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    async def get_by_id(self, job_id: str) -> RefreshJob | None:
        """ジョブIDで取得"""
        stmt = select(RefreshJobModel).where(RefreshJobModel.job_id == job_id)
        result = self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update(self, job: RefreshJob) -> RefreshJob:
        """ジョブを更新"""
        stmt = select(RefreshJobModel).where(RefreshJobModel.job_id == job.job_id)
        result = self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            raise ValueError(f"Job not found: {job.job_id}")

        model.status = job.status
        model.processed_count = job.processed_count
        model.succeeded_count = job.succeeded_count
        model.failed_count = job.failed_count
        model.errors = json.dumps(job.errors) if job.errors else None
        model.started_at = job.started_at
        model.completed_at = job.completed_at

        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    async def get_latest(self, limit: int = 10) -> list[RefreshJob]:
        """最新のジョブを取得"""
        stmt = (
            select(RefreshJobModel)
            .order_by(RefreshJobModel.created_at.desc())
            .limit(limit)
        )
        result = self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    def _to_entity(self, model: RefreshJobModel) -> RefreshJob:
        """モデルをエンティティに変換"""
        errors = None
        if model.errors:
            try:
                errors = json.loads(model.errors)
            except json.JSONDecodeError:
                errors = []

        return RefreshJob(
            job_id=model.job_id,
            status=model.status,
            source=model.source,
            total_symbols=model.total_symbols,
            processed_count=model.processed_count,
            succeeded_count=model.succeeded_count,
            failed_count=model.failed_count,
            errors=errors,
            started_at=model.started_at,
            completed_at=model.completed_at,
            created_at=model.created_at,
        )
