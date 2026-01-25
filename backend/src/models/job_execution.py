"""ジョブ実行 モデル"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.connection import Base


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

    def __repr__(self) -> str:
        return (
            f"<JobExecution("
            f"flow_id={self.flow_id}, "
            f"job_name={self.job_name}, "
            f"status={self.status}"
            f")>"
        )
