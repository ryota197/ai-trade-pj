"""MarketBenchmark SQLAlchemyモデル"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.connection import Base


class MarketBenchmarkModel(Base):
    """
    市場ベンチマークモデル

    対応テーブル: market_benchmarks
    """

    __tablename__ = "market_benchmarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False)

    performance_1y: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    performance_9m: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    performance_6m: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    performance_3m: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    performance_1m: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    weighted_performance: Mapped[float | None] = mapped_column(
        Numeric(10, 4), nullable=True
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<MarketBenchmark(symbol={self.symbol}, weighted_perf={self.weighted_performance})>"
