"""Trade モデル"""

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.connection import Base


class TradeType(Enum):
    """トレードタイプ"""

    BUY = "buy"
    SELL = "sell"


class TradeStatus(Enum):
    """トレードステータス"""

    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class Trade(Base):
    """
    ペーパートレード

    trades テーブルに対応するSQLAlchemyモデル。
    """

    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False, index=True)

    # トレード情報
    trade_type: Mapped[str] = mapped_column(String(10), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    exit_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    # ステータス
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")

    # タイムスタンプ
    traded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<Trade("
            f"id={self.id}, "
            f"symbol={self.symbol}, "
            f"type={self.trade_type}, "
            f"status={self.status}"
            f")>"
        )
