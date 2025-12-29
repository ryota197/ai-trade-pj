"""StockPrice SQLAlchemyモデル"""

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.connection import Base


class StockPriceModel(Base):
    """
    価格スナップショットモデル

    対応テーブル: stock_prices
    """

    __tablename__ = "stock_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("stocks.symbol", ondelete="CASCADE"),
        nullable=False,
    )

    price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    change_percent: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    volume: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    avg_volume_50d: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    market_cap: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    week_52_high: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    week_52_low: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<StockPrice(symbol={self.symbol}, price={self.price})>"
