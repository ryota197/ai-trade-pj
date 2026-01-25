"""ウォッチリスト モデル"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.connection import Base


class Watchlist(Base):
    """
    ウォッチリストモデル

    CAN-SLIMスクリーニングで見つけた監視銘柄を保存。
    """

    __tablename__ = "watchlist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 銘柄情報
    symbol: Mapped[str] = mapped_column(
        String(10), nullable=False, unique=True, index=True
    )

    # 目標価格
    target_entry_price: Mapped[float | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    stop_loss_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    target_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    # メモ
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ステータス
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="watching", index=True
    )
    triggered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # メタデータ
    added_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Watchlist("
            f"symbol={self.symbol}, "
            f"status={self.status}, "
            f"target_entry={self.target_entry_price}"
            f")>"
        )
