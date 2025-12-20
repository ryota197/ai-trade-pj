"""株価キャッシュ SQLAlchemyモデル"""

from datetime import datetime, timezone

from sqlalchemy import Date, DateTime, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.connection import Base


class PriceCacheModel(Base):
    """
    株価キャッシュモデル

    日次の株価データ（OHLCV）をキャッシュして、
    外部API呼び出しを削減する。
    """

    __tablename__ = "price_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 銘柄・日付（複合ユニーク制約）
    symbol: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)

    # OHLCV
    open: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    high: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    low: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    close: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    volume: Mapped[int] = mapped_column(Integer, nullable=False)

    # メタデータ
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # 複合ユニーク制約
    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_price_cache_symbol_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<PriceCache("
            f"symbol={self.symbol}, "
            f"date={self.date}, "
            f"close={self.close}"
            f")>"
        )
