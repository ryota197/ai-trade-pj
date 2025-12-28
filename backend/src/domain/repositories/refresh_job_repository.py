"""リフレッシュジョブ リポジトリインターフェース"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RefreshJob:
    """リフレッシュジョブエンティティ"""

    job_id: str
    status: str  # pending, running, completed, failed, cancelled
    source: str  # sp500, nasdaq100, custom
    total_symbols: int
    processed_count: int
    succeeded_count: int
    failed_count: int
    errors: list[dict] | None  # [{"symbol": "XYZ", "error": "..."}]
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class RefreshJobRepository(ABC):
    """リフレッシュジョブ リポジトリインターフェース"""

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
