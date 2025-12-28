"""リフレッシュジョブ SQLAlchemyモデル"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.connection import Base


class RefreshJobModel(Base):
    """
    リフレッシュジョブモデル

    スクリーニングデータ更新ジョブの状態を管理する。
    """

    __tablename__ = "refresh_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ジョブ識別子
    job_id: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )

    # ジョブ情報
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="custom")

    # 進捗
    total_symbols: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    succeeded_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # エラー情報（JSON配列として文字列保存）
    errors: Mapped[str | None] = mapped_column(Text, nullable=True)

    # タイミング
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<RefreshJob("
            f"job_id={self.job_id}, "
            f"status={self.status}, "
            f"progress={self.processed_count}/{self.total_symbols}"
            f")>"
        )

    @property
    def percentage(self) -> float:
        """進捗率を計算"""
        if self.total_symbols == 0:
            return 0.0
        return (self.processed_count / self.total_symbols) * 100
