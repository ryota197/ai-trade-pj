"""ジョブ実行 モデル"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.adapters.database import Base


class JobExecution(Base):
    """
    ジョブ実行モデル（子）

    フロー内の各ジョブの実行状態を管理する。
    複合主キー: (flow_id, job_name)
    """

    __tablename__ = "job_executions"

    # 複合主キー
    flow_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("flow_executions.flow_id", ondelete="CASCADE"),
        primary_key=True,
    )
    job_name: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    # ジョブ情報
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )

    # タイミング
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # 結果
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # === エンティティメソッド ===

    def start(self) -> None:
        """ジョブ開始"""
        self.status = "running"
        self.started_at = datetime.now(timezone.utc)

    def complete(self, result: dict | None = None) -> None:
        """ジョブ完了"""
        self.status = "completed"
        self.completed_at = datetime.now(timezone.utc)
        self.result = result

    def fail(self, error_message: str) -> None:
        """ジョブ失敗"""
        self.status = "failed"
        self.completed_at = datetime.now(timezone.utc)
        self.error_message = error_message

    def skip(self) -> None:
        """ジョブスキップ"""
        self.status = "skipped"

    @property
    def duration_seconds(self) -> float | None:
        """実行時間（秒）"""
        if self.started_at is None:
            return None
        end = self.completed_at or datetime.now(timezone.utc)
        return (end - self.started_at).total_seconds()

    def __repr__(self) -> str:
        return (
            f"<JobExecution("
            f"flow_id={self.flow_id}, "
            f"job_name={self.job_name}, "
            f"status={self.status}"
            f")>"
        )
