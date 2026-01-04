"""フロー・ジョブ実行エンティティ"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class FlowStatus(str, Enum):
    """フロー実行状態"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobStatus(str, Enum):
    """ジョブ実行状態"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class FlowExecution:
    """
    フロー実行（親）

    RefreshScreenerFlow等のフロー全体の実行状態を管理する。
    """

    flow_id: str
    flow_name: str  # 'refresh_screener'
    status: FlowStatus = FlowStatus.PENDING
    total_jobs: int = 3
    completed_jobs: int = 0
    current_job: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def start(self, first_job: str) -> None:
        """フロー開始"""
        self.status = FlowStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
        self.current_job = first_job

    def advance(self, next_job: str | None) -> None:
        """次のジョブへ進む"""
        self.completed_jobs += 1
        self.current_job = next_job

    def complete(self) -> None:
        """フロー完了"""
        self.status = FlowStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.current_job = None

    def fail(self) -> None:
        """フロー失敗"""
        self.status = FlowStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)

    @property
    def duration_seconds(self) -> float | None:
        """実行時間（秒）"""
        if self.started_at is None:
            return None
        end = self.completed_at or datetime.now(timezone.utc)
        return (end - self.started_at).total_seconds()


@dataclass
class JobExecution:
    """
    ジョブ実行（子）

    フロー内の各ジョブの実行状態を管理する。
    複合主キー: (flow_id, job_name)
    """

    flow_id: str
    job_name: str  # 'collect_stock_data', 'calculate_rs_rating', 'calculate_canslim'
    status: JobStatus = JobStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict | None = None
    error_message: str | None = None

    def start(self) -> None:
        """ジョブ開始"""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)

    def complete(self, result: dict | None = None) -> None:
        """ジョブ完了"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.result = result

    def fail(self, error_message: str) -> None:
        """ジョブ失敗"""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        self.error_message = error_message

    def skip(self) -> None:
        """ジョブスキップ"""
        self.status = JobStatus.SKIPPED

    @property
    def duration_seconds(self) -> float | None:
        """実行時間（秒）"""
        if self.started_at is None:
            return None
        end = self.completed_at or datetime.now(timezone.utc)
        return (end - self.started_at).total_seconds()
