"""StockMetrics SQLAlchemyモデル"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.connection import Base


class StockMetricsModel(Base):
    """
    計算指標モデル

    対応テーブル: stock_metrics
    """

    __tablename__ = "stock_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("stocks.symbol", ondelete="CASCADE"),
        nullable=False,
    )

    # ファンダメンタル
    eps_growth_quarterly: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    eps_growth_annual: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    institutional_ownership: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )

    # RS関連
    relative_strength: Mapped[float | None] = mapped_column(
        Numeric(10, 4), nullable=True
    )
    rs_rating: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    # CAN-SLIMスコア
    canslim_score: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True
    )

    calculated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<StockMetrics(symbol={self.symbol}, rs_rating={self.rs_rating})>"
