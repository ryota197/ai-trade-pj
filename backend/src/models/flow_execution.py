"""フロー実行 モデル"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.adapters.database import Base


class FlowExecution(Base):
    """
    フロー実行モデル（親）

    RefreshScreenerFlow等のフロー全体の実行状態を管理する。
    """

    __tablename__ = "flow_executions"

    # 主キー
    flow_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
    )

    # フロー情報
    flow_name: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )

    # 進捗サマリ
    total_jobs: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    completed_jobs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_job: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # タイミング
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # === エンティティメソッド ===

    def start(self, first_job: str) -> None:
        """フロー開始"""
        self.status = "running"
        self.started_at = datetime.now(timezone.utc)
        self.current_job = first_job

    def advance(self, next_job: str | None) -> None:
        """次のジョブへ進む"""
        self.completed_jobs += 1
        self.current_job = next_job

    def complete(self) -> None:
        """フロー完了"""
        self.status = "completed"
        self.completed_at = datetime.now(timezone.utc)
        self.current_job = None

    def fail(self) -> None:
        """フロー失敗"""
        self.status = "failed"
        self.completed_at = datetime.now(timezone.utc)

    @property
    def duration_seconds(self) -> float | None:
        """実行時間（秒）"""
        if self.started_at is None:
            return None
        end = self.completed_at or datetime.now(timezone.utc)
        return (end - self.started_at).total_seconds()

    def __repr__(self) -> str:
        return (
            f"<FlowExecution("
            f"flow_id={self.flow_id}, "
            f"flow_name={self.flow_name}, "
            f"status={self.status}, "
            f"progress={self.completed_jobs}/{self.total_jobs}"
            f")>"
        )
