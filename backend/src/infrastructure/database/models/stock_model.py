"""Stock SQLAlchemyモデル"""

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.connection import Base


class StockModel(Base):
    """
    銘柄モデル

    CAN-SLIMスクリーニング対象の銘柄データを保存。
    """

    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 銘柄基本情報
    symbol: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # 株価情報
    price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    change_percent: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    volume: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    avg_volume_50d: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    market_cap: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    week_52_high: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    week_52_low: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    # CAN-SLIM指標
    eps_growth_quarterly: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    eps_growth_annual: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    institutional_ownership: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )

    # RS関連（Job 1, 2 で更新）
    relative_strength: Mapped[float | None] = mapped_column(
        Numeric(10, 4), nullable=True
    )
    rs_rating: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    # CAN-SLIMスコア（Job 3 で更新）
    canslim_score: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True
    )

    # メタデータ
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Stock("
            f"symbol={self.symbol}, "
            f"rs_rating={self.rs_rating}, "
            f"canslim_score={self.canslim_score}"
            f")>"
        )
