"""フロー実行 モデル"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.connection import Base


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

    def __repr__(self) -> str:
        return (
            f"<FlowExecution("
            f"flow_id={self.flow_id}, "
            f"flow_name={self.flow_name}, "
            f"status={self.status}, "
            f"progress={self.completed_jobs}/{self.total_jobs}"
            f")>"
        )
